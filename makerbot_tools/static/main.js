/*jslint unparam: true */
/*global window, $ */
$(function () {

$.fn.extend({
    showFiles: function (data) {
        container = this;
        container.empty()
        $.each(data, function (index, file) {
            node = $(
                '<p class="file">' + file.name + ' ' +
                // '<a class="btn btn-info btn-small"' +
                // '   href="' + file.print_url + '">print</a>' +
                '</p>'
            );
            node.appendTo(container);
        });
        return container;
    },
    getFiles: function () {
        node = this;
        $.get('/api/files', function(data) {
            node.showFiles(data.files);
        });
        return node;
    },
    showJobs: function (data) {
        container = this;
        container.empty()
        $.each(data, function (index, item) {
            node = $(
                '<p class="job">' + item + ' ' +
                '</p>'
            );
            node.appendTo(container);
        });
        return container;
    },
    getJobs: function () {
        node = this;
        $.get('/api/jobs', function(data) {
            if (data.success && data.result) {
                node.showJobs(data.result);
            }
            setTimeout(function () { node.getJobs() }, 3000);
        });
        return node;
    },
    showPrinter: function (printer) {
        $('a.brand').text(
            printer.displayName + ' - ' +
            printer.uniqueName + ' ' +
            '(' + printer.state + ') '
        );
        return this;
    },
    getPrinter: function () {
        node = this;
        $.get('/api/connect', function(data) {
            if (data.success && data.result) {
                node.showPrinter(data.result);
            }
            setTimeout(function () { node.getPrinter() }, 3000);
        });
        return node;
    }
});

$('#progress, #error').hide();
$('a.brand').getPrinter();
//$('#jobs').getJobs();
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
