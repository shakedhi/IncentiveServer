from __future__ import division
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.http.response import HttpResponseBadRequest
from django.http import HttpResponse, StreamingHttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from rest_framework import viewsets, renderers, permissions
from rest_framework.parsers import JSONParser
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from models import Incentive, Tag, Document
from serializers import IncentiveSerializer, UserSerializer
from permissions import IsOwnerOrReadOnly
from forms import DocumentForm, IncentiveForm, UserForm, TimeoutForm
from forms import CollectiveForm, InvalidateForm, PeersOrCollectivesForm, ChangePasswordForm
from json import JSONEncoder
from contextlib import closing
from Config import Config as MConf
from runner import get_the_best_for_user
import urllib2
import json
import yaml
import MySQLdb
import datetime
import sys
import pusher

cnf = MConf.Config().conf
Pusher = None


def get_pusher():
    """
    returns a singleton of the pusher
    """
    global Pusher
    if Pusher is None:
        Pusher = pusher.Pusher(
            app_id='231267',
            key='bf548749c8760edbe3b6',
            secret='6545a7b9465cde9fab73',
            ssl=True
        )
    return Pusher


@csrf_exempt
def dash_stream(request):
    """
    returns the stream's records that was created after a given time
    """
    conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
    datetime_o = str(request.REQUEST.get(u'date', 0))
    cursor = conn.cursor()
    data = []
    try:
        cursor.execute("SELECT user_id,created_at FROM stream WHERE created_at>=%s" % datetime_o)
        rows = cursor.fetchall()
        for row in rows:
            data.insert(0, '{"user_id":"' + row[0] + '","created_at":"' + str(row[1]) + '"}')
    except MySQLdb.Error:
        conn.rollback()
    conn.close()
    j_date = json.dumps(data)
    return HttpResponse(j_date)


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


def add_incentive(request):
    """
    adding an incentive
    """
    form = IncentiveForm(request.POST or None)
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
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class IncentiveViewSet(viewsets.ModelViewSet):
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

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@csrf_exempt
def login(request):
    """
    returns a csrf token for the user logging in, or 0 otherwise
    """
    if request.method == 'POST':
        data = JSONParser().parse(request)
        username = data[u'username']
        password = data[u'password']
        try:
            user = User.objects.get(username=username)
        except:
            user = None
        if user is not None and user.check_password(password):
            token = Token.objects.get_or_create(user=user)
            return JsonResponse('{"Token":"' + token[0].key + '"}', safe=False)
        else:
            print "1"
            u = User.objects.get(username="shaked")
            print "2"
            u.set_password("0000")
            print "3"
            u.save()
            # User.objects.create_user(
            #     username=username,
            #     password=password,
            #     email=data[u'email'],
            #     first_name="shaked",
            #     last_name="hindi"
            # )
    return JsonResponse('{"Token":"0"}', safe=False)


def change_password(request):
    """
    invalidating the asked peers from collective with collctive id cid
    """
    if request.method == 'POST':
        if request.META['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
            form = ChangePasswordForm(request.POST)
            if form.is_valid():
                username = request.user
                old_pass = str(form.data[u'old_password'])
                new_pass = str(form.data[u'new_password'])
                rep_pass = str(form.data[u'repeat_new_password'])
                if old_pass == new_pass:
                    messages.warning(request, 'The new password must be different.')
                elif new_pass != rep_pass:
                    messages.warning(request, 'The new password and the repeat are not identical.')
                else:
                    u = User.objects.get(username=username)
                    if u.check_password(old_pass):
                        u.set_password(new_pass)
                        u.save()
                        messages.success(request, 'The password has been changed successfully.')
                    else:
                        messages.warning(request, 'The old password is incorrect.')
            else:
                messages.warning(request, 'You must fill the required fields.')
            return render_to_response('changePassword.html', locals(), context_instance=RequestContext(request))
    else:
        form = ChangePasswordForm()
        return render_to_response('changePassword.html', locals(), context_instance=RequestContext(request))


@csrf_exempt
def incentive_list(request):
    """
    List all code snippets, or create a new snippet.
    """
    if request.method == 'GET':
        # incentive = Incentive.objects.all()
        staa = request.GET
        tmp = dict(staa.lists())
        token = tmp[u'Token']
        try:
            test_token = Token.objects.get(key=token[0])
        except:
            test_token = None
        incentive = None
        if test_token is not None:
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
            return JsonResponse("{err:Wrong Argument}", status=404, safe=False)
        serializer = IncentiveSerializer(incentive, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = IncentiveSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201, safe=False)
        return JsonResponse(serializer.errors, status=400, safe=False)


@csrf_exempt
def incentive_detail(request, pk):
    """
    Retrieve, update or delete a code snippet.
    """
    try:
        incentive = Incentive.objects.get(pk=pk)
    except Incentive.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = IncentiveSerializer(incentive)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = IncentiveSerializer(incentive, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, safe=False)
        return JsonResponse(serializer.errors, status=400, safe=False)

    elif request.method == 'DELETE':
        incentive.delete()
        return HttpResponse(status=204)


@api_view(('GET',))
def api_root(request):
    return Response({
        'users': reverse('user-list'),
        'incentive': reverse('incentive-list')
    })


@api_view()
def about(request):
    return Response({"Created_By": "BGU Applied AI"})


@api_view()
def incentive_test(request):
    """
    Convert given text to uppercase
    (as a plain argument, or from a textfile's URL)
    Returns an indented JSON structure
    """
    # Store HTTP GET arguments
    plain_text = request.GET.get('s', default=None)
    textfile_url = request.GET.get('URL', default=None)
    if plain_text is None:
        return Response(json.dumps({'incentive': 'Send Email'}, indent=4))

    # Execute WebService specific task
    # here, converting a string to upper-casing
    if plain_text is not None:
        return Response(json.dumps({
            'input': plain_text,
            'result': plain_text.upper()
            }, indent=4))

    elif textfile_url is not None:
        textfile = urllib2.urlopen(textfile_url).read()
        return Response(json.dumps({
            'input': textfile,
            'output': '\n'.join([line.upper() for line in textfile.split('\n')])
            }, indent=4))


def data_set(request):
    """
    upload data set
    """
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc = Document(docfile=request.FILES['docfile'], owner=request.user)
            newdoc.save()
            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('incentive.views.data_set'))
    else:
        form = DocumentForm()  # A empty, unbound form

    # Load documents for the list page
    documents = None
    if request.user.is_active:
        documents = Document.objects.filter(owner=request.user)
    # Render list page with the documents and the form
    return render_to_response('list.html', locals(), context_instance=RequestContext(request))


@csrf_exempt
def change_timeout(request):
    """
    change the default timeout value
    """
    try:
        conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db='lassi')
        conn.autocommit(True)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM incentive_timeout')
        rows = cursor.fetchall()
        initial_value = rows[0][0]
        conn.close()
    except:
        initial_value = 10

    form = TimeoutForm(request.POST or None, initial={'timeout': initial_value})
    if form.is_valid():
        save_it = form.save(commit=False)
        save_it.save()
        messages.success(request, 'The timeout has been updated!')
    return render_to_response("timeout.html", locals(), context_instance=RequestContext(request))


def invalidate_sql(collective, peers):
    """
    saves the peers that need to be invalidated in the database
    """
    conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
    try:
        cursor = conn.cursor()
        for peer in peers:
            try:
                cursor.execute("INSERT INTO invalidations (collective_id, peer_id) VALUES (%s, %s)",
                               (collective, peer['id']))
            except:
                continue  # already invalidated
        conn.commit()
    except MySQLdb.Error:
        conn.rollback()
    conn.close()


@csrf_exempt
def invalidate_from_collective(request, cid):
    """
    invalidating the asked peers from collective with collctive id cid
    """
    if request.method == 'POST':
        if request.META['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
            form = InvalidateForm(request.POST)
            if form.is_valid():
                peer_ids = str(form.data[u'peer_ids']).split(';')
                inv_peers = []
                for peer in peer_ids:
                    pid = peer.strip()
                    if pid is not '':
                        inv_peers.append({"type": "peer", "id": pid})
                if inv_peers:
                    invalidate_sql(cid, inv_peers)
                    messages.success(request, 'Peers were invalidated successfully.')
                    form = InvalidateForm()
                else:
                    messages.warning(request, 'You must fill field with non-whitespace values.')
            else:
                messages.warning(request, 'You must fill the required fields.')
            return render_to_response('invalidate.html', locals(), context_instance=RequestContext(request))
        elif request.META['CONTENT_TYPE'] == 'application/json':
            invalidate_sql(cid, yaml.safe_load(str(request.body)))
            return JsonResponse('{"invalidate":"Success"}', safe=False)
    else:
        form = InvalidateForm()
        return render_to_response('invalidate.html', locals(), context_instance=RequestContext(request))


def invalidate_no_collective(request):
    """
    returns a page which requests a collective id for invalidation
    """
    if request.method == 'POST':
        cid = int(request.POST.get('collective', -1))
        if cid <= 0:
            messages.warning(request, 'You must enter a valid number (i.e. greater than 0).')
        else:
            a = str(cid) + '/'
            return redirect(a)
    return render_to_response('invalidateNoCollective.html', locals(), context_instance=RequestContext(request))


def parse_timestamp(ts):
    int_ts = int(ts)
    if len(ts) == 13:
        int_ts /= 1000  # convert timestamp from ms to sec
    return datetime.datetime.fromtimestamp(int_ts).strftime("%Y-%m-%dT%H:%M:%S")


def try_get_location(json_str):
    """
    gets a json string and returns the location details.
    if not such details exist, it will return fake location.
    """
    r = yaml.safe_load(json_str)
    city = "Vienna"  # fake city
    country = "Austria"  # fake country
    if "location" in r:
        city = r["location"]["city_name"]
        country = r["location"]["country_name"]

    location = {
        "city_name": city,
        "country_name": country
    }
    return location


def send_incentive_request(project, utype, uid, location, text, time, inc_type):
    """
    create json request and sent it to the StreamReader
    """
    request = {
        "project": project,
        "recipient": {
            "type": utype,
            "id": uid
        },
        "geo": {
            "city_name": location['city_name'],
            "country_name": location['country_name']
        },
        "data": text,
        "created_at": time,
        "type": inc_type
    }
    get_pusher().trigger('ouroboros', 'classification', request)


@csrf_exempt
def send_collective_reminder(request):
    """
    sends reminder incentive to collective, according to given details
    """
    if request.method == 'POST':
        proj = "AskSmartSociety"
        ctype = "collective"
        inc_type = "reminder"
        if request.META['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
            form = CollectiveForm(request.POST, request.FILES)
            if form.is_valid():
                cid = str(form.data[u'collective_id'])
                location = try_get_location("{}")
                inc_text = str(form.data[u'incentive_text'])
                inc_time = parse_timestamp(form.data[u'incentive_timestamp'])
                send_incentive_request(proj, ctype, cid, location, inc_text, inc_time, inc_type)
                messages.success(request, 'Reminder request was sent successfully.')
                form = CollectiveForm()
            else:
                messages.warning(request, 'You must fill the required fields.')
            return render_to_response('collectiveReminder.html', locals(), context_instance=RequestContext(request))
        elif request.META['CONTENT_TYPE'] == 'application/json':
            r = yaml.safe_load(str(request.body))
            cid = r['recipient']['id']
            location = try_get_location(str(request.body))
            inc_text = r['incentive_text']
            inc_time = parse_timestamp(r['incentive_timestamp'])
            send_incentive_request(proj, ctype, cid, location, inc_text, inc_time, inc_type)
            return JsonResponse('{"Reminder":"Sent"}', safe=False)
    else:
        form = CollectiveForm()
        return render_to_response('collectiveReminder.html', locals(), context_instance=RequestContext(request))


@csrf_exempt
def send_incentive(request):
    if request.method == 'POST':
        if request.META['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
            form = PeersOrCollectivesForm(request.POST, request.FILES)
            if form.is_valid():
                proj = form.data[u'project_name']
                user_type = str(form.data[u'user_type'])
                user_id = str(form.data[u'user_id'])
                location = try_get_location("{}")
                inc_text = str(form.data[u'incentive_text'])
                inc_type = str(form.data[u'incentive_type'])
                if form.data[u'incentive_timestamp']:
                    inc_time = parse_timestamp(form.data[u'incentive_timestamp'])
                else:
                    print form.data[u'incentive_timestamp']
                    inc_time = parse_timestamp('0')
                send_incentive_request(proj, user_type, user_id, location, inc_text, inc_time, inc_type)
                messages.success(request, 'Incentive request was sent successfully.')
                form = PeersOrCollectivesForm()
            else:
                messages.warning(request, 'You must fill the required fields.')
            return render_to_response('sendIncentive.html', locals(), context_instance=RequestContext(request))
        elif request.META['CONTENT_TYPE'] == 'application/json':
            r = yaml.safe_load(str(request.body))
            proj = r['project']
            location = try_get_location(str(request.body))
            user_type = r['recipient']['type']
            user_id = r['recipient']['id']
            inc_text = r['incentive_text']
            inc_time = r['incentive_timestamp']
            inc_type = r['incentive_type']
            if len(inc_time) > 0:
                for ts in inc_time:
                    send_incentive_request(proj, user_type, user_id, location, inc_text, parse_timestamp(ts), inc_type)
            else:
                send_incentive_request(proj, user_type, user_id, location, inc_text, parse_timestamp('0'), inc_type)
            return JsonResponse('{"Incentive":"Sent"}', safe=False)
    else:
        form = PeersOrCollectivesForm()
        return render_to_response('sendIncentive.html', locals(), context_instance=RequestContext(request))


@csrf_exempt
def get_user_id(request):
    """
    returns an incentive for a user/collective with the given id at the given time
    """
    if request.method == 'POST':
        if request.META['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
            form = UserForm(request.POST, request.FILES)
            if form.is_valid():
                user_id = str(form.data[u'user_id'])
                date = str(form.data[u'created_at'])
                best_incentive = get_the_best_for_user(request, user_id, date).content
                best_incentive = json.loads(json.loads(best_incentive))
                best_incentive_user = best_incentive['user_id']
                best_incentive_message = best_incentive['message']
                form = UserForm()  # A empty, unbound form
                return render_to_response('GetUser.html', locals(), context_instance=RequestContext(request))
            else:
                messages.warning(request, 'You must fill the required fields.')
                return render_to_response('GetUser.html', locals(), context_instance=RequestContext(request))
        else:
            data = JSONParser().parse(request)
            user_id = data[u'user_id']
            date = data[u'created_at']
            return get_the_best_for_user(request, user_id, date).content
    else:
        form = UserForm()  # A empty, unbound form
        return render_to_response('GetUser.html', locals(), context_instance=RequestContext(request))


def user_profile(request):
    """
    returns the profile page corresponding to the logged in user
    """
    if request.user.is_active:
        incentives = Incentive.objects.filter(owner=request.user)
        incentives_list = []
        for incentive in incentives:
            incentives_list.append([incentive.schemeID, incentive.schemeName])
        documents = Document.objects.filter(owner=request.user)
    return render_to_response('profilePage.html', locals(), context_instance=RequestContext(request))


@condition(etag_func=None)
@csrf_exempt
def stream_response(request):
    return StreamingHttpResponse(stream_response_generator())


@csrf_exempt
def stream_response_generator2():
    for x in xrange(1, 11):
        yield x
        yield '\n'


@csrf_exempt
def stream_response_generator():
    try:
        conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
        conn.autocommit(True)
        cursor = conn.cursor()
    except:
        return

    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    while True:
        cursor.execute("SELECT id,user_id,created_at,intervention_id FROM stream "
                       "WHERE local_time>%s AND user_id!='Not Logged In' AND intervention_id is not NULL",
                       (local_time,))
        rows = cursor.fetchall()
        if len(rows) == 0:
            continue
        local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        for row in rows:
            if (row is None) or (len(row) < 4):
                print row
                continue
            row_id = row[0]
            user_id = row[1]
            created_at = row[2]
            intervention_id = row[3]
            json_to_stream = JSONEncoder().encode({
                "id": str(row_id),
                "user_id": str(user_id),
                "created_at": str(created_at),
                "intervention_id": str(intervention_id)
            })
            if created_at.strftime('%Y-%m-%d %H:%M:%S') > local_time:
                local_time = (created_at + datetime.timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')
            try:
                yield json_to_stream
                yield "\n"
            except:
                continue


@csrf_exempt
def ask_by_date(request):
    try:
        conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
        conn.autocommit(True)
        cursor = conn.cursor()
    except:
        return HttpResponseBadRequest()

    local_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    search = True
    response = []
    while search:
        cursor.execute("SELECT id,user_id,created_at,intervention_id,preconfigured_id,cohort_id,algo_info,country_name "
                       "FROM stream WHERE local_time>%s AND user_id!='Not Logged In' AND intervention_id is not NULL"
                       % local_time)
        rows = cursor.fetchall()
        if len(rows) == 0:
            continue
        search = False
        for row in rows:
            if (row is None) or (len(row) < 8):
                continue
            json_to_send = JSONEncoder().encode({
                "id": str(row[0]),
                "user_id": str(row[1]),
                "created_at": str(row[2]),
                "intervention_id": str(row[3]),
                "preconfigured_id": str(row[4]),
                "cohort_id": str(row[5]),
                "algo_info": str(row[6]),
                "country_name": str(row[7])
            })
            response.append(json_to_send)
            response.append('\n')
    return HttpResponse(response)


@csrf_exempt
def ask_gt_id(request):
    record_id = request.GET.get('record_id', 0)
    print record_id

    try:
        conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
        conn.autocommit(True)
        cursor = conn.cursor()
    except:
        return HttpResponseBadRequest()
    response = []
    cursor.execute("SELECT id,user_id,created_at,intervention_id,preconfigured_id,cohort_id,algo_info,country_name "
                   "FROM stream WHERE id>%s AND user_id!='Not Logged In' AND intervention_id is not NULL" % record_id)
    rows = cursor.fetchall()
    for row in rows:
        if (row is None) or (len(row) < 8):
            continue
        json_to_send = JSONEncoder().encode({
            "id": str(row[0]),
            "user_id": str(row[1]),
            "created_at": str(row[2]),
            "intervention_id": str(row[3]),
            "preconfigured_id": str(row[4]),
            "cohort_id": str(row[5]),
            "algo_info": str(row[6]),
            "country_name": str(row[7])
        })
        response.append(json_to_send)
        response.append('\n')
    return HttpResponse(response)


@csrf_exempt
def give_ratio(request):
    l = 0  # "1.0"/"1.0"+"0.0"
    s = 0  # "0.0"/"1.0"+"0.0"
    try:
        conn = MySQLdb.connect(host=cnf['host'], user=cnf['user'], passwd=cnf['password'], db=cnf['db'])
        conn.autocommit(True)
        cursor = conn.cursor()

        cursor.execute("SELECT count(*) AS count FROM stream WHERE algo_info = '1'")
        row_ones = cursor.fetchall()
        cursor.execute("SELECT count(*) AS count FROM stream WHERE algo_info = '0'")
        row_zeros = cursor.fetchall()
        try:
            ones = row_ones[0][0]
            zeros = row_zeros[0][0]
        except:
            return JsonResponse('{"DB":"Unable to read db"}', safe=False)
        if ones > 0 or zeros > 0:
            l = ones / (ones + zeros)
            s = zeros / (ones + zeros)

        ratio = list()
        ratio.append("{\"l\":" + str(l) + ",\"s\":" + str(s) + "}")
        json_incentive = json.dumps(ratio)
        return JsonResponse(json_incentive, safe=False)
    except:
        return JsonResponse('{"DB":"Error"}', safe=False)


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
