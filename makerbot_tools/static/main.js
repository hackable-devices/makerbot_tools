/*jslint unparam: true */
/*global window, $ */
$(function () {

$.fn.extend({
    showFiles: function (data) {
        files = this;
        files.empty()
        $.each(data, function (index, file) {
            node = $(
                '<p>' + file.name + ' ' +
                '<a class="btn btn-info btn-small"' +
                '   href="' + file.print_url + '">print</a>' +
                '</p>'
            );
            node.appendTo('#files');
        });
        return files;
    },
    getFiles: function () {
        files = this;
        $.get('/api/files', function(data) {
            files.showFiles(data.files);
        });
        return files;
    }
});

$('#progress, #error').hide();
$('#files').getFiles();
$('#fileupload').fileupload({
    url: '/upload',
    type: "PUT",
    multipart: true,
    dataType: 'json',
    done: function (e, data) {
        $('#files').showFiles(data.result.files);
        $('#progress').hide();
    },
    fail: function (e, data) {
        $('#error').text('Bad request').show();
        $('#progress').hide();
        setTimeout(function() { $('#error').hide()}, 3000);
    },
    progressall: function (e, data) {
        var progress = parseInt(data.loaded / data.total * 100, 10);
        $('#progress').show();
        $('#progress .bar').css('width', progress + '%');
    }
});

});
