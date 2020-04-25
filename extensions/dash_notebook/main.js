// file my_extension/main.js

define([
    'base/js/namespace',
    'base/js/utils',
], function(Jupyter, utils){

    function load_ipython_extension(){
        console.info('this is my first extension');

        var notebookUrl = window.location.href
        var baseUrl = utils.get_body_data('baseUrl');
        var baseNotebooks = baseUrl + "notebooks"
        var n = notebookUrl.search(baseNotebooks)
        var jupyterServerUrl = notebookUrl.slice(0, n)
        console.log(jupyterServerUrl)
        console.log(baseUrl)

        Jupyter.notebook.kernel.comm_manager.register_target('jupyter_dash',
        function(comm, msg) {
            // Register handlers for later messages:
            comm.on_msg(function(msg) {
                var msgData = msg.content.data;
                console.log(msgData)
                if (msgData.type === 'base_url_request') {
                    comm.send({
                        type: 'base_url_response',
                        server_url: jupyterServerUrl,
                        base_subpath: baseUrl,
                        frontend: "notebook"
                    });
                }
            });
        });
    }

    return {
        load_ipython_extension: load_ipython_extension
    };
});
