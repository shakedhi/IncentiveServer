from __future__ import division
from django.contrib import messages

from django.contrib.auth.models import User, Group
from django.http.response import HttpResponseNotFound, HttpResponseBadRequest
from rest_framework import viewsets
from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from models import Incentive, Tag
from serializers import IncentiveSerializer, UserSerializer
from rest_framework.decorators import detail_route
from rest_framework import renderers, permissions, status, generics, mixins
from permissions import IsOwnerOrReadOnly
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from StringIO import StringIO
import urllib2, json
from rest_framework.authtoken.models import Token

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from models import Document
from forms import DocumentForm
import MySQLdb
from forms import IncentiveFrom
from json import JSONEncoder
import datetime
from Predictor import dis_predictor
from contextlib import closing
import sys


@csrf_exempt
def dashStream(request):
    conn = MySQLdb.connect(host="localhost", user="root", passwd="9670", db="streamer")
    datetimeO = str(request.REQUEST.dicts[0][u'date'])
    cursor = conn.cursor()
    try:
        data = []
        cursor.execute("SELECT user_id,created_at FROM stream WHERE created_at>=%s" % (datetimeO))

        rows = cursor.fetchall()
        for row in rows:
            data.insert(0, '{"user_id":"' + row[0] + '","created_at":"' + str(row[1]) + '"}')


    except MySQLdb.Error as e:
        conn.rollback()
    conn.close()
    jDate = json.dumps(data)
    return HttpResponse(jDate)


def home(request):
    return render_to_response("signups.html", locals(), context_instance=RequestContext(request))


def thankyou(request):
    return render_to_response("thankyou.html", locals(), context_instance=RequestContext(request))


@csrf_exempt
def dash(request):
    return render_to_response("dash/pages/dash.html", locals(), context_instance=RequestContext(request))


def wiki(request):
    return render_to_response("wiki.html", locals(), context_instance=RequestContext(request))


def aboutus(request):
    return render_to_response("aboutus.html", locals(), context_instance=RequestContext(request))


def addIncentive(request):
    form = IncentiveFrom(request.POST or None)
    if form.is_valid():
        save_it = form.save(commit=False)
        save_it.save()
        messages.success(request, 'Your Incentive Has been saved')
    return render_to_response("IncentiveForm.html", locals(), context_instance=RequestContext(request))


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class IncetiveViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Additionally we also provide an extra `highlight` action.
    """
    queryset = Incentive.objects.all()
    serializer_class = IncentiveSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)

    @detail_route(renderer_classes=[renderers.StaticHTMLRenderer])
    def highlight(self, request, *args, **kwargs):
        incentive = self.get_object()
        return Response(incentive.highlighted)

    # def perform_create(self, serializer):
    #         serializer.save()
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


# class IncentiveHighlight(generics.GenericAPIView):
#     queryset = Incentive.objects.all()
#     renderer_classes = (renderers.StaticHTMLRenderer,)
#
#     def get(self, request, *args, **kwargs):
#         incentive = self.get_object()
#         return Response(incentive.highlighted)

class IncentiveView(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    queryset = Incentive.objects.all()
    serializer_class = IncentiveSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        usernames = [incentive.status for incentive in Incentive.objects.all()]
        return Response(usernames)


@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        username = data[u'username']
        password = data[u'password']
        user = None
        try:
            user = User.objects.get(username=username)
        except:
            pass
        if user is not None and user.check_password(password):
            token = Token.objects.get_or_create(user=user)
            return JSONResponse("{'Token':'" + token[0].key + "'}")
    return JSONResponse("{'Token':'0'}")


@csrf_exempt
def incetive_list(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        # incentive = Incentive.objects.all()
        staa = request.GET
        tmp = dict(staa.lists())
        token = tmp[u'Token']
        t = str(token[0])
        testToken = None
        try:
            testToken = Token.objects.get(key=token[0])
        except:
            testToken = None
        incentive = None
        if (testToken is not None):
            for key in tmp:
                if key == 'tagID':
                    tags = Tag.objects.filter(tagID=tmp[key][0])
                    incentive = Incentive.objects.filter(tags=tags)
                if key == 'status':
                    incentive = Incentive.objects.filter(status=tmp[key])
                if key == 'groupIncentive':
                    incentive = Incentive.objects.filter(groupIncentive=tmp[key])
                if key == 'typeID':
                    incentive = Incentive.objects.filter(typeID=tmp[key][0])
                if key == 'schemeID':
                    incentive = Incentive.objects.filter(schemeID=tmp[key][0])
        if incentive is None:
            return JSONResponse("{err:Wrong Argument}", status=404)
        serializer = IncentiveSerializer(incentive, many=True)
        return JSONResponse(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = IncentiveSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        return JSONResponse(serializer.errors, status=400)


@csrf_exempt
def incetive_detail(request, pk):
    """
    Retrieve, update or delete a code snippet.
    """
    try:
        incentive = Incentive.objects.get(pk=pk)
    except Incentive.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = IncentiveSerializer(incentive)
        return JSONResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = IncentiveSerializer(incentive, data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data)
        return JSONResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        incentive.delete()
        return HttpResponse(status=204)


@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'incentive': reverse('incentive-list', request=request, format=format),
    })


# @api_view()
# def xml(request):
#     o="Fail-PATH: "
#     o+=os.path.dirname(__file__)
#     o+='/Text.xml'
#     fileName=os.path.dirname(__file__)+'/Test.xml'
#     if os.path.isfile(fileName):
#         with open(fileName,'r') as f:
#            str = f.read().replace('\n', '')
#         o= xmltodict.parse(str)
#     return Response(json.dumps(o))


@api_view()
def about(request):
    return Response({"Created_By": "BGU Applied AI"})


@api_view()
def incentiveTest(request):
    """
    Convert given text to uppercase
    (as a plain argument, or from a textfile's URL)
    Returns an indented JSON structure
    """

    # Store HTTP GET arguments
    plain_text = request.GET.get('s', default=None)
    textfile_url = request.GET.get('URL', default=None)
    io = StringIO()
    if plain_text is None:
        return Response(json.dumps(
            {'incentive': "Send Email"
             },
            indent=4))

    # Execute WebService specific task
    # here, converting a string to upper-casing
    if plain_text is not None:
        return Response(json.dumps(
            {'input': plain_text,
             'result': plain_text.upper()
             },
            indent=4))

    elif textfile_url is not None:
        textfile = urllib2.urlopen(textfile_url).read()
        return Response(json.dumps(
            {'input': textfile,
             'output': '\n'.join([line.upper() for line in textfile.split('\n')])
             },
            indent=4))


def list(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = Document(docfile=request.FILES['docfile'], owner=request.user)
            newdoc.save()

            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('incentive.views.list'))
    else:
        form = DocumentForm()  # A empty, unbound form

    # Load documents for the list page
    documents = None
    if request.user.is_active:
        documents = Document.objects.filter(owner=request.user)

    # Render list page with the documents and the form
    return render_to_response('list.html', locals(), context_instance=RequestContext(request))


from runner import getTheBestForTheUser
from forms import getUserForm


@csrf_exempt
def getUserID(request):
    if request.method == 'POST':
        form = getUserForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = str(form.data[u'userID'])
            date = str(form.data[u'created_at'])
            BestIncentive = getTheBestForTheUser(request, newdoc, date).content
            # Redirect to the document list after POST
            # Render list page with the documents and the form
            return HttpResponse(json.dumps(BestIncentive))
            # return render_to_response('GetUser.html', locals(), context_instance=RequestContext(request))
    else:
        form = getUserForm()  # A empty, unbound form
        return render_to_response('GetUser.html', locals(), context_instance=RequestContext(request))


def userProfile(request):
    # Load documents for the list page
    incentivesList = []
    incentives = None
    if request.user.is_active:
        incentives = Incentive.objects.filter(owner=request.user)
        for incentive in incentives:
            incentivesList.append(str(incentive.schemeID) + ":" + incentive.schemeName)
        documents = Document.objects.filter(owner=request.user)
        # user=User.objects.get(username=request.user)

    return render_to_response(
        'profilePage.html', locals(),
        context_instance=RequestContext(request)
    )


from django.views.decorators.http import condition


class Config(object):
    conf = dict()
    # conf['clfFile'] ='/home/ise/Model/dismodel.pkl'
    # conf['clfFile'] ='/Users/avisegal/models/dtew/dismodel.pkl'
    conf['clfFile'] = '/home/eran/Documents/Lassi/src/Algorithem/Model/dismodel.pkl'

    # conf['strmLog'] = '/home/ise/Logs/streamer.log'
    conf['strmLog'] = '/home/shaked/Documents/Logs/streamer.log'

    # conf['predLog'] = '/home/ise/Logs/predictor.log'
    conf['predLog'] = '/home/shaked/Documents/Logs/predictor.log'

    # conf['dis_predLog'] = '/home/ise/Logs/dis_predictor.log'
    conf['dis_predLog'] = '/home/shaked/Documents/Logs/dis_predictor.log'

    conf['debug'] = False

    conf['user'] = 'root'

    conf['password'] = '656544'

    conf['host'] = 'localhost'

    conf['db'] = 'streamer'


cnf = Config().conf


@condition(etag_func=None)
@csrf_exempt
def stream_response(request):
    resp = StreamingHttpResponse(stream_response_generator())
    return resp


@csrf_exempt
def stream_response_generator2():
    for x in xrange(1, 11):
        yield x
        yield '\n'


@csrf_exempt
def stream_response_generator():
    try:
        conn = MySQLdb.connect(host="localhost", user="root", passwd="9670", db="streamer")
        conn.autocommit(True)
        cursor = conn.cursor()
    except:
        return
    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    while True:
        cursor.execute(
            'SELECT id,user_id,created_at,intervention_id FROM stream WHERE (local_time>"%s") and intervention_id is Not NULL' % local_time)
        rows = cursor.fetchall()
        if len(rows) == 0:
            continue
        local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        for row in rows:
            if (row is None) or (len(row) < 4):
                print row
                continue
            id = row[0]
            user_id = row[1]
            created_at = row[2]
            intervention_id = row[3]
            jsonToStream = JSONEncoder().encode({
                "id": str(id),
                "user_id": str(user_id),
                "created_at": str(created_at),
                "intervention_id": str(intervention_id)
            })
            if created_at.strftime('%Y-%m-%d %H:%M:%S') > local_time:
                local_time = (created_at + datetime.timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')
            try:
                yield jsonToStream
                yield "\n"
            except:
                continue


@csrf_exempt
def ask_by_date(request):
    try:
        conn = MySQLdb.connect(host="localhost", user="root", passwd="9670", db="streamer")
        conn.autocommit(True)
        cursor = conn.cursor()
    except:
        return HttpResponseBadRequest()
    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    search = True
    response = []
    while search:
        cursor.execute(
            'SELECT id,user_id,created_at,intervention_id,preconfigured_id,cohort_id,algo_info,country_name FROM stream WHERE (local_time>"%s")  and (user_id!="Not Logged In") and intervention_id is Not NULL' % local_time)
        rows = cursor.fetchall()
        if len(rows) == 0:
            continue
        search = False
        for row in rows:
            if (row is None) or (len(row) < 8):
                continue
            id = row[0]
            user_id = row[1]
            created_at = row[2]
            intervention_id = row[3]
            preconfigured_id = row[4]
            cohort_id = row[5]
            algo_info = row[6]
            country_name = row[7]
            jsonToSend = JSONEncoder().encode({
                "id": id,
                "user_id": str(user_id),
                "created_at": str(created_at),
                "intervention_id": str(intervention_id),
                "preconfigured_id": str(preconfigured_id),
                "cohort_id": str(cohort_id),
                "algo_info": str(algo_info),
                "country_name": str(country_name)
            })
            response.append(jsonToSend)
            response.append('\n')
    return HttpResponse(response)


@csrf_exempt
def ask_gt_id(request):
    record_id = request.GET['record_id']

    print record_id

    try:
        conn = MySQLdb.connect(host="localhost", user="root", passwd="9670", db="streamer")
        conn.autocommit(True)
        cursor = conn.cursor()
    except:
        return HttpResponseBadRequest()
    response = []
    cursor.execute(
        'SELECT id,user_id,created_at,intervention_id,preconfigured_id,cohort_id,algo_info,country_name FROM stream WHERE (id>"%s") and (user_id!="Not Logged In") and intervention_id is Not NULL' % record_id)
    rows = cursor.fetchall()
    for row in rows:
        if (row is None) or (len(row) < 8):
            continue
        id = row[0]
        user_id = row[1]
        created_at = row[2]
        intervention_id = row[3]
        preconfigured_id = row[4]
        cohort_id = row[5]
        algo_info = row[6]
        country_name = row[7]
        jsonToSend = JSONEncoder().encode({
            "id": id,
            "user_id": str(user_id),
            "created_at": str(created_at),
            "intervention_id": str(intervention_id),
            "preconfigured_id": str(preconfigured_id),
            "cohort_id": str(cohort_id),
            "algo_info": str(algo_info),
            "country_name": str(country_name)
        })
        response.append(jsonToSend)
        response.append('\n')
    return HttpResponse(response)


@csrf_exempt
def GiveRatio(request):
    print "Give Ratio Requested"
    ones = 0
    zeros = 0
    l = 0  # "1.0"/"1.0"+"0.0"
    s = 0  # "0.0"/"1.0"+"0.0"
    try:
        conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
        conn.autocommit(True)
        cursor = conn.cursor()

        cursor.execute('SELECT  count(*) AS count  FROM stream WHERE algo_info =  "1"')
        rows = cursor.fetchall()
        if len(rows) == 0:
            return JSONResponse('{"DB":"Unable to read db"}')
        for row in rows:
            try:
                ones = row[0]
            except:
                return JSONResponse('{"DB":"Unable to read db"}')

        cursor.execute('SELECT  count(*) AS count  FROM stream WHERE algo_info =  "0"')
        rows = cursor.fetchall()
        if len(rows) == 0:
            return JSONResponse('{"DB":"Unable to read db"}')
        for row in rows:
            try:
                zeros = row[0]
            except:
                return JSONResponse('{"DB":"Unable to read db"}')
        if ones > 0 or zeros > 0:
            l = ones / (ones + zeros)
            s = zeros / (ones + zeros)

        ratio = []
        ratio.append("{\"l\":" + str(l) + ",\"s\":" + str(s) + "}")
        jsonIncentive = json.dumps(ratio)
        print jsonIncentive
        return JSONResponse(jsonIncentive)
    except:
        return JSONResponse('{"DB":"Error"}')


def sql(query, params):
    # connect
    conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
    with closing(conn.cursor()) as cursor:
        try:
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except:
            print sys.exc_info()
            conn.rollback()
            conn.close()
            return False


@csrf_exempt
def receive_event(request):
    try:
        received_json_data = json.loads(request.body)
        source = received_json_data['source']
        event_type = received_json_data['event_type']
        timestamp = received_json_data['timestamp']
        user_id = received_json_data['user_id']
        experiment_name = received_json_data['experiment_name']
        project = received_json_data['project']
        if 'additional_info' in received_json_data:
            additional_info = received_json_data['additional_info']
        else:
            additional_info = None
        if sql(
                """INSERT INTO events (source,event_type,timestamp,user_id,experiment_name,project,additional_info) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (source, event_type, timestamp, user_id, experiment_name, project, additional_info)):
            return HttpResponse("OK")
        else:
            return HttpResponseBadRequest("Unable to save event.")
    except:
        print sys.exc_info()
        return HttpResponseBadRequest("Malformed Data!")
