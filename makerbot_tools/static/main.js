/*jslint unparam: true */
/*global window, $ */
$('#progress, #error').hide();

function PrinterCtrl($scope, $http) {
    $scope.timeout = 3000;
    $scope.title = 'Loading...';

    $scope.printer = {
        displayName: 'Loading...',
        uniqueName: '',
        state: 'IDLE' // 'DISCONNECTED'
    }

    $scope.idle = function() { return $scope.printer.state === 'IDLE'; }

    $scope.jobs = [];

    $scope.files = [];
    $http.get('/api/files').success(function(data) {
        if (data.files) {
            $scope.files = data.files;
        }
    });

    $scope.refresh = function() {
        $http.get('/api/connect').success(function(data) {
            if (data.success && data.result) {
                var p = data.result, t = null;
                $scope.printer = p;
                t =  p.displayName + ' ' + p.uniqueName + ' (' + p.state + ')';
                $scope.title = t;
                $('title').text(t);
                if (!$scope.idle()) {
                    $http.get('/api/jobs').success(function(data) {
                        if (data.success && data.result) {
                            $scope.jobs = data.result;
                        }
                        $scope.set_timeout()
                    }).error($scope.set_timeout);
                } else { $scope.set_timeout() }
            } else { $scope.set_timeout() }
        }).error($scope.set_timeout);
    }
    $scope.set_timeout = function() {
        // setTimeout($scope.refresh, $scope.timeout);
    }
    // $scope.refresh()

    $scope.remove = function(e) {
        $(e.target).parent('div').remove();
    }

    $('#fileupload').fileupload({
        url: '/upload',
        type: "PUT",
        multipart: true,
        dataType: 'json',
        done: function (e, data) {
            $scope.files = data.result.files;
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

};

