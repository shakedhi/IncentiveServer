/**
 * Created by dor on 4/19/15.
 */


function checklogin() {
    var username = document.getElementById("inputEmail").value;
    var passd = document.getElementById("inputPassword").value;
    $.ajax({
        data: {"username": username, "passwd": passd},
        url: 'checklogin.php',
        async: false,
        method: 'POST', // or GET
        success: function (msg) {
            if (msg == true) {

            }

        },
        error: function (jqXHR, error, errorThrown) {
            console.log(error)
        }
    });
}