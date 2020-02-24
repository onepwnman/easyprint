// websocket server
let socket = io.connect('ws://your_server_ip_here:12000');

// webcam server
let serverAddress = 'http://your_server_ip_here:5001/?action=stream';

socket.on('notify', function(msg) {
    notification(msg.type, msg.title, msg.text, msg.icon);
});

$('.usage').on('click', function() {
    $('#usage-modal').modal('toggle');
  
});

$(document).ready(function () {
  $('#print-result-table').DataTable({
    "pagingType": "first_last_numbers", // "simple" option for 'Previous' and 'Next' buttons only
		"paging": true,
  });
  $('.dataTables_length').addClass('bs-select');
});

socket.on('alarm', function(msg) {
    var html = '';
    html += '<a class="nav-link" data-toggle="dropdown" href="#">';
    html += '<i class="far fa-bell"></i>';
    html += '</a>';
    html += '<span class="badge badge-warning navbar-badge">' + msg.unchecked_count + '</span>'
    html += '<div class="dropdown-menu dropdown-menu-lg dropdown-menu-right">';
    html += '<span class="dropdown-item dropdown-header">' + msg.unchecked_count + ' Notifications</span>'
    html += '<div class="dropdown-divider"></div>';
    html += '<a href="printer/result" class="dropdown-item checked-link">';
    html += '<i class="fas fa-clipboard-check">Check it out! ' + msg.unchecked_count + ' Printing Job is Done.</i>'
    html += '</a>';
    html += '<a href="printer/result" class="dropdown-item dropdown-footer checked-link">See All Notifications</a>';
    html += '</div>';
    $('#alarm-bell').html(html);
});

$('#reg_submit').on('click', function() {
    if ($('#reg_agree_on_terms')[0].checked != true) {
        notification('notice', 'You must agree on terms before register account','','fas fa-file-alt');
        location.href = '#terms-end';
        return false;
    } 
});


function convertHMS(value) {
    const sec = parseInt(value, 10); // convert value to number if it's string
    let hours   = Math.floor(sec / 3600); // get hours
    let minutes = Math.floor((sec - (hours * 3600)) / 60); // get minutes
    let seconds = sec - (hours * 3600) - (minutes * 60); //  get seconds
    // add 0 if value < 10
    if (hours   < 10) {hours   = "0"+hours;}
    if (minutes < 10) {minutes = "0"+minutes;}
    if (seconds < 10) {seconds = "0"+seconds;}
    return hours+':'+minutes+':'+seconds; // Return is HH : MM : SS
}


if(window.document.getElementById('printing-area')) {
    /* --------- DROPZONE INSTANCE --------- */
    const DROPZONE = new Dropzone("#dropzone", {
        clickable: '#addFiles',
        acceptedFiles: '.stl',
        maxFilesize: 3, //MB
        parallelUploads: 5,
        previewTemplate: document.getElementById("template").innerHTML
    });


    /* --------- SELECTABLE INSTANCE --------- */
    const SELECTABLE = new Selectable({
        appendTo: "#dropzone",
        ignore: "[data-dz-remove]", // stop remove button triggering selection
        lasso: {
            border: "1px solid rgba(155, 155, 155,1.0)",
            backgroundColor: "rgba(255, 255, 255,0.4)"
        }
    }); 
    
    // Global modeling variable to make only one model instance on the page
    var modelFlag = true;
    var modelPath, modelPosition, modelList = {};
      
    function renderModel() {
        if (modelPath) {
            try {
                var isModel = $("#model-wrapper > div.active").attr("id");
                modelFlag = false;
            } catch (e) {
            }
            var $div = $('<div id="model" class="model-size"></div>');
            $("#model-wrapper").html($div);
            STLViewer(modelPath, modelPosition);
            
        }
    }


    /* --------- BUTTONS --------- */
    const removeFiles = document.getElementById("removeFiles");
    removeFiles.classList.add('active');

    removeFiles.addEventListener("click", e => {
        const files = DROPZONE.files;
        if ( files.length ) {
            for ( const file of files ) {
                DROPZONE.removeFile(file);
            }
        }
    });

    
    /* --------- SELECTABLE EVENTS --------- */
    var selectedModel;
    function selectFile() {
        if (selectedModel) {
          var temp = selectedModel;
          SELECTABLE.deselect(selectedModel);
        }
        selectedModel = SELECTABLE.getSelectedItems()[0];
        
        if (selectedModel) {
            var fileName = selectedModel.node.getElementsByClassName('file-name')[0].innerText
            modelPath = modelList[fileName];
            renderModel();
        } else {
            selectedModel = temp;
            SELECTABLE.select(temp);
        }
    }

    SELECTABLE.on("end", selectFile);


    function selectOnly(fileName) {
        var files = DROPZONE.files;
        var prevSelected = SELECTABLE.getSelectedItems()[0];

        if (prevSelected) {
            SELECTABLE.deselect(prevSelected);
        }
        for (file of files) {
            if (file.name == fileName) {
                selectedModel = SELECTABLE.get(file.previewElement);
                SELECTABLE.select(selectedModel);
            }
        }
    }
    

    /* --------- DROPZONE EVENTS --------- */
    DROPZONE.on("addedfile", function(file, event) {
        if ($('.login-form')[0]) {
            notification('notice', 'login requierd', 'please login!', 'fas fa-sign-in-alt');
            DROPZONE.removeAllFiles(true);
            return false;
        }

        if (file.name.length > 64) {
            notification('notice', 'File name Too long', '', 'fas fa-exclamation-triangle');
            DROPZONE.removeAllFiles(true);
            return false;
        }
            

        const el = file.previewElement;
        
				if (modelList) {
						for (var element in modelList){
								if (element == file.name){
										DROPZONE.removeFile(file);
                    selectOnly(file.name);
                    modelPath = modelList[element];
                    renderModel();
										return false;
								}
						}
				}
			
        // add element to Selectable instance when added by Dropzone
        SELECTABLE.add(el);
        
        file.previewElement.querySelector(".file-progress-text").textContent = "Ready";
        file.previewElement.querySelector(".file-text").textContent = "Waiting";
        
        // bounce animation
        el.classList.add("animated", "bounceIn");
        setTimeout(() => {
            el.classList.remove("animated", "bounceIn");
        }, 550);    
    });

    DROPZONE.on("removedfile", function(file) {
        const el = file.previewElement;
        
        // remove element from Selectable instance when removed by Dropzone
        SELECTABLE.remove(el);
    });

    // this is just for the upload progress indicator
    DROPZONE.on("uploadprogress", (file, progress) => {
            if ($('.login-form')[0]) {
                notification('notice', 'Login requierd', 'Please Login!', 'fas fa-sign-in-alt');
                return false;
            }
            const el = file.previewElement;
            const circle = el.querySelector("circle");
            const r = circle.getAttribute("r");
            const circ = 2 * Math.PI * r;   
            const p = Math.round(progress);
            
            circle.style.strokeDashoffset = circ - (circ * (progress / 100));
            
            el.classList.remove("loading");
            el.querySelector(".mdi").classList.add("mdi-upload");
            el.querySelector(".file-progress-text").textContent = file.mock ? `Done` : `Processing`;    
            el.querySelector(".file-text").textContent = p === 100 ? `Uploaded` : `Uploading ${p}%`;    
    });


    DROPZONE.on("complete", function(file) {
        if ($('.login-form')[0]) {
            notification('notice', 'Login requierd', 'Please Login!', 'fas fa-sign-in-alt');
            return false;
        }
        const el = file.previewElement;
        const mdi = el.querySelector(".mdi");
        
        mdi.classList.remove("mdi-upload");
        mdi.classList.add("mdi-check");
        if (el.querySelector(".file-progress-text").textContent != `Error`) {
            el.querySelector(".file-progress-text").textContent = `Upload complete`;
        }

        var response = JSON.parse(arguments[0].xhr.response);

        modelPath = response.path, modelPosition = response.elementID;
        modelList[response.original_file] = modelPath;

        var files = DROPZONE.files;
        for (file of files) {
            if (file.name == response.original_file){
                if (selectedModel){
                    SELECTABLE.deselect(SELECTABLE.getSelectedItems()[0]);
                }
                selectedModel = SELECTABLE.get(file.previewElement);
                SELECTABLE.select(selectedModel);
            }
        }

        notification('success', 'File successfully uploaded!', '', 'fas fa-file-upload');
        renderModel();
    });


    DROPZONE.on("error", function(file, message, xhr) {
        const el = file.previewElement;
        const mdi = el.querySelector(".mdi");
        
        mdi.classList.remove("mdi-upload");
        mdi.classList.add("mdi-close");
        el.querySelector(".file-progress-text").textContent = `Error`;
        el.querySelector(".file-text").textContent = "Not allowed";
    });


    let printing = false;
    let camera = 'off';
    var elapsedTime;
    var timerInterrupt;
    timerInterrupt = setInterval(function() {
        if ($('#elapsed-time').length){
            elapsedTime += 1;
            $('#elapsed-time').html('<span id="elapsed-time">Elapsed time: ' + convertHMS(elapsedTime) + '</span>');
        }
    }, 1000);
    socket.on('print', function(msg) {
        try {
              var data = JSON.parse(msg)
              // For current printing status
              var currentPrinting = data[0];
              var html = '';
              html += '<h5 class="card-header">Print Status</h5>';
              html += '<div class="card-body p-0">';
              html += '<label for="printing-status" class="pt-3 pb-1 pl-3"> Current Print</label>';
              html += '<div class="p-0" id="printing-status">';
              html += '<ul class="list-group list-group-flush">';
              html += '<li class="list-group-item waiting-list">';
              html += '<div id="print-date">';
              html += '<span>File: ' + currentPrinting['filename'] + '</span></br>';
              html += '<span>User: ' + currentPrinting['username'] + '</span></br>';
              html += '<span>Added time: ' + currentPrinting['added_time'] + '</span></br>';
              html += '<span>Estimated printing time: ' + convertHMS(currentPrinting['estimated_time_second']) + '</span></br>';
              html += '<hr>';

              if (currentPrinting['current_layer'] == 0){
                  html += '<span>Ready for print, heating up the print bed!</br>';
              } else {
                  html += '<span>Layer: ' + currentPrinting['current_layer'] + '/' + currentPrinting['total_layer'] + '</span><br>';
                  elapsedTime = currentPrinting['started_time_second'];
                  html += '<span id="elapsed-time">Elapsed time: ' + convertHMS(elapsedTime) + '</span></br>';
                  html += '<div class="pt-2">';
                  html += '<div class="progress">';
                  html += '<div class="progress-bar progress-bar-striped progress-bar-animated custom-progress-bar" role="progressbar"';
                  var progress = parseInt(currentPrinting['current_layer'] / currentPrinting['total_layer'] * 100);
                  if (progress >= 100) {
                      progress = 100;
                  }
                  html += 'aria-valuenow="' + progress + '" aria-valuemin="0" aria-valuemax="100" style="width: ' + progress + '%">' + progress + '%</div>';
                  html += '</div>';
                  html += '</div>';
                  html += '</div>';
              }
              html += '</ul>';
              html += '</li>';

              // For printing waiting list
              elementCountPerPage = 3;
              if (data.length > 1){
                  html += '<label for="print-waiting-list" id="waiting-list-label" class="pt-3 pb-1 pl-3"> Waiting List</label>';
                  html += '<div id="print-waiting-list">';
                  for (var i = 1 ; i < elementCountPerPage + 1 ; i++) {
                      if (data[i]) {
                          var waitingObj = data[i];
                          html += '<ul class="list-group list-group-flush">';
                          html += '<li class="list-group-item waiting-list">';
                          // only uploaded user can delete the print list 
                          var userName = $('#user-name').text().trim();
                          if (userName.length && waitingObj['username'] == userName) {
                              html += '<button type="button" class="delete-from-list close" data-dismiss="modal" aria-label="Close">';
                              html += '<span aria-hidden="true">&times;</span>'
                              html += '</button>'
                          }
                          
                          html += '<span>File: ' + waitingObj['filename'] + '</span></br>';
                          html += '<span class="waiting-list-user">User: ' + waitingObj['username'] + '</span></br>';
                          html += '<span class="waiting-list-added-time">Added time: ' + waitingObj['added_time'] + '</span></br>';
                          html += '<span>Estimated printing time: ' + convertHMS(waitingObj['estimated_time_second']) + '</span></br>';
                          html += '</li>';
                          html += '</ul>';

                      }
                  }
                  html += '</div>';
              } 
              $('#printing-status').html(html);
              
              if ($('.delete-from-list').length) {
                  $('.delete-from-list').on('click', function(event) {
                      var ulElement = event.target.closest('ul');
                      if (!ulElement) return;
                      var userString = ulElement.getElementsByClassName('waiting-list-user')[0].innerText;
                      var addedTimeString = ulElement.getElementsByClassName('waiting-list-added-time')[0].innerText;
                      var user = userString.split('User: ')[1];
                      var addedTime = addedTimeString.split('Added time: ')[1];
                      var data = {};
                      data['user'] = user;
                      data['added_time'] = addedTime;
                      socket.emit('delete', data);
                      ulElement.remove();
                      if (!$('#print-waiting-list').find('ul').length){
                          $('#print-waiting-list').remove();
                          $('#waiting-list-label').remove();
                      }
                  });
              } else {
                  $('.delete-from-list').off('click');
              }

        }  
        catch (e) {
            $('#printing-status').html('<h5 class="card-header">Print Status</h5>' +
                '<img src="/static/img/need-work.jpg" class="card-img-top blur-img" alt="">');
        }    
    });


    var options = {};
    var fileInfo = {}; 
    var progressInfo;

    socket.on('slice', function(msg) {
        if (msg.state == 'success'){
            fileInfo['estimatedTime'] = msg.TIME; 
            $("#modalLongTitle").text("Slicing Result of " + msg.fileName);
            $("#modalList").html("<li class=\"list-group-item\">Layer Hight: " +
                msg['Layer height'] + "</li>" + "<li class=\"list-group-item\">Estimated Printing Time: " + convertHMS(msg.TIME) + "</li>" + "<li class=\"list-group-item\">Estimated Filament Usage: " + msg['Filament used'] + "</li>");
            $("#printModal").modal('toggle');

            options.title = 'Done!';
            options.text = 'Successfully Sliced'
            options.type = 'success';
            options.icon = 'fas fa-check-circle';
            options.width = "350px";
            options.hide = true;
            options.shadow = true;
            progressInfo.update(options);
            progressInfo.on('click', function() {
                progressInfo.close();
            });
        } else if (msg.state == 'fail') {
            progressInfo.close();
            notification(msg.type, msg.title, msg.text, msg.icon);
        }
        $("#slice").removeAttr('disabled');
        $('#slice').html('Slice<i class="pl-1 fab fa-slack-hash"></i>');
    });

    $("#slice").on("click", function(event) {
        if (selectedModel){
            // checking upload complete
            progressElement = selectedModel.node.getElementsByClassName('file-progress-text')
            if (progressElement[0].innerText != 'Upload complete') {
                notification('notice', 'File not uploaded', '', 'fas fa-file-upload');
            }

            
            if (selectedModel)
            var targetFile = selectedModel.node.getElementsByClassName('file-name')[0].innerText;
            fileInfo = {'originalFileName': targetFile, 'fileName': modelList[targetFile].split('/').pop(), 
								'quality': $("#qualitySelect").val(), 'infill': $("#densitySelect").val() };


            var showProgressNote = function() {
                return PNotify.info({
                    text: 'Please wait for Slicing is done!',
                    icon: 'fas fa-spinner fa-pulse',
                    hide: false,
                    shadow: false,
										width: '300px',
                    modules: {
                      Buttons: {
                        closer: false,
                        sticker: false
                      }
                    }
                  });
            }
            progressInfo = showProgressNote();
            progressInfo.on('click', function() {
                progressInfo.close();
            });

            options = {};
            $("#slice").attr('disabled', '');
            $('#slice').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Slicing...');

            socket.emit('slice', fileInfo) 


        } else {
            notification('notice', 'File not selected!', 'Please select the printing target', 'fas fa-exclamation-triangle');
        }
    });


    var updateWebcamPanel = function() {
        var html = '';
        var webcamWidth = 0;
        var webcamHeight = 0;

        webcamWidth = $('#webcam').width();
        webcamHeight = webcamWidth * 3 / 4;

        if (camera == 'off') {
            html += '<div class="img" style="height:' + webcamHeight + 'px">';
            html += '<div class="content">';
            html += '<p>Waiting for printing...</p>';
            html += '</div>';
            html += '<div class="img-cover"></div> ';
            html += '</div>';
        } else if (camera == 'on') {
            html += '<img src="' + serverAddress + '" width="' + webcamWidth + '" height="' + webcamHeight + '">';
        }
        $('#webcam').html(html);
    };
    updateWebcamPanel();

    let adjustWebcam = function(){
        setTimeout(updateWebcamPanel, 350);
    }

		socket.on('camera', function(msg) {
				if (msg.button == 'on') {
						camera = 'on';
						$('#webcam-power').html('<i class="fas fa-toggle-on"></i>');
						updateWebcamPanel();
				} else if (msg.button == 'off') {
						camera = 'off';
						$('#webcam-power').html('<i class="fas fa-toggle-off"></i>');
						updateWebcamPanel();
				}
		});

    $('#webcam-power').on('click', function() {
            if (camera == 'on') {
                $('#webcam-power').html('<i class="fas fa-toggle-off"></i>');
                camera = 'off';
            } else if (camera == 'off') {
                $('#webcam-power').html('<i class="fas fa-toggle-on"></i>');
                camera = 'on';
            }
            updateWebcamPanel();
    });


    $('#startPrint').on('click', function() {
				$('#printModal').modal('hide')
        socket.emit('print', fileInfo);

        socket.on('print', function(msg) {
            
        });
    });


    // For Resize STLViewer Pannel
    (function($,window,undefined){
      '$:nomunge'; // Used by YUI compressor.
      
      // A jQuery object containing all non-window elements to which the resize
      // event is bound.
      var elems = $([]),
        
        // Extend $.resize if it already exists, otherwise create it.
        jq_resize = $.resize = $.extend( $.resize, {} ),
        
        timeout_id,
        
        // Reused strings.
        str_setTimeout = 'setTimeout',
        str_resize = 'resize',
        str_data = str_resize + '-special-event',
        str_delay = 'delay',
        str_throttle = 'throttleWindow';
      
      // Property: jQuery.resize.delay
      // 
      // The numeric interval (in milliseconds) at which the resize event polling
      // loop executes. Defaults to 250.
      
      jq_resize[ str_delay ] = 250;
      
      // Property: jQuery.resize.throttleWindow
      // 
      // Throttle the native window object resize event to fire no more than once
      // every <jQuery.resize.delay> milliseconds. Defaults to true.
      // 
      // Because the window object has its own resize event, it doesn't need to be
      // provided by this plugin, and its execution can be left entirely up to the
      // browser. However, since certain browsers fire the resize event continuously
      // while others do not, enabling this will throttle the window resize event,
      // making event behavior consistent across all elements in all browsers.
      // 
      // While setting this property to false will disable window object resize
      // event throttling, please note that this property must be changed before any
      // window object resize event callbacks are bound.
      
      jq_resize[ str_throttle ] = true;
      
      // Event: resize event
      // 
      // Fired when an element's width or height changes. Because browsers only
      // provide this event for the window element, for other elements a polling
      // loop is initialized, running every <jQuery.resize.delay> milliseconds
      // to see if elements' dimensions have changed. You may bind with either
      // .resize( fn ) or .bind( "resize", fn ), and unbind with .unbind( "resize" ).
      // 
      // Usage:
      // 
      // > jQuery('selector').bind( 'resize', function(e) {
      // >   // element's width or height has changed!
      // >   ...
      // > });
      // 
      // Additional Notes:
      // 
      // * The polling loop is not created until at least one callback is actually
      //   bound to the 'resize' event, and this single polling loop is shared
      //   across all elements.
      // 
      // Double firing issue in jQuery 1.3.2:
      // 
      // While this plugin works in jQuery 1.3.2, if an element's event callbacks
      // are manually triggered via .trigger( 'resize' ) or .resize() those
      // callbacks may double-fire, due to limitations in the jQuery 1.3.2 special
      // events system. This is not an issue when using jQuery 1.4+.
      // 
      // > // While this works in jQuery 1.4+
      // > $(elem).css({ width: new_w, height: new_h }).resize();
      // > 
      // > // In jQuery 1.3.2, you need to do this:
      // > var elem = $(elem);
      // > elem.css({ width: new_w, height: new_h });
      // > elem.data( 'resize-special-event', { width: elem.width(), height: elem.height() } );
      // > elem.resize();
          
      $.event.special[ str_resize ] = {
        
        // Called only when the first 'resize' event callback is bound per element.
        setup: function() {
          // Since window has its own native 'resize' event, return false so that
          // jQuery will bind the event using DOM methods. Since only 'window'
          // objects have a .setTimeout method, this should be a sufficient test.
          // Unless, of course, we're throttling the 'resize' event for window.
          if ( !jq_resize[ str_throttle ] && this[ str_setTimeout ] ) { return false; }
          
          var elem = $(this);
          
          // Add this element to the list of internal elements to monitor.
          elems = elems.add( elem );
          
          // Initialize data store on the element.
          $.data( this, str_data, { w: elem.width(), h: elem.height() } );
          
          // If this is the first element added, start the polling loop.
          if ( elems.length === 1 ) {
            loopy();
          }
        },
        
        // Called only when the last 'resize' event callback is unbound per element.
        teardown: function() {
          // Since window has its own native 'resize' event, return false so that
          // jQuery will unbind the event using DOM methods. Since only 'window'
          // objects have a .setTimeout method, this should be a sufficient test.
          // Unless, of course, we're throttling the 'resize' event for window.
          if ( !jq_resize[ str_throttle ] && this[ str_setTimeout ] ) { return false; }
          
          var elem = $(this);
          
          // Remove this element from the list of internal elements to monitor.
          elems = elems.not( elem );
          
          // Remove any data stored on the element.
          elem.removeData( str_data );
          
          // If this is the last element removed, stop the polling loop.
          if ( !elems.length ) {
            clearTimeout( timeout_id );
          }
        },
        
        // Called every time a 'resize' event callback is bound per element (new in
        // jQuery 1.4).
        add: function( handleObj ) {
          // Since window has its own native 'resize' event, return false so that
          // jQuery doesn't modify the event object. Unless, of course, we're
          // throttling the 'resize' event for window.
          if ( !jq_resize[ str_throttle ] && this[ str_setTimeout ] ) { return false; }
          
          var old_handler;
          
          // The new_handler function is executed every time the event is triggered.
          // This is used to update the internal element data store with the width
          // and height when the event is triggered manually, to avoid double-firing
          // of the event callback. See the "Double firing issue in jQuery 1.3.2"
          // comments above for more information.
          
          function new_handler( e, w, h ) {
            var elem = $(this),
              data = $.data( this, str_data );
            
            // If called from the polling loop, w and h will be passed in as
            // arguments. If called manually, via .trigger( 'resize' ) or .resize(),
            // those values will need to be computed.
            data.w = w !== undefined ? w : elem.width();
            data.h = h !== undefined ? h : elem.height();
            
            old_handler.apply( this, arguments );
          };
          
          // This may seem a little complicated, but it normalizes the special event
          // .add method between jQuery 1.4/1.4.1 and 1.4.2+
          if ( $.isFunction( handleObj ) ) {
            // 1.4, 1.4.1
            old_handler = handleObj;
            return new_handler;
          } else {
            // 1.4.2+
            old_handler = handleObj.handler;
            handleObj.handler = new_handler;
          }
        }
        
      };
      
      function loopy() {
        
        // Start the polling loop, asynchronously.
        timeout_id = window[ str_setTimeout ](function(){
          
          // Iterate over all elements to which the 'resize' event is bound.
          elems.each(function(){
            var elem = $(this),
              width = elem.width(),
              height = elem.height(),
              data = $.data( this, str_data );
            
            // If element size has changed since the last time, update the element
            // data store and trigger the 'resize' event.
            if ( width !== data.w || height !== data.h ) {
              elem.trigger( str_resize, [ data.w = width, data.h = height ] );
            }
            
          });
          
          // Loop.
          loopy();
          
        }, jq_resize[ str_delay ] );
        
      };
      
    })(jQuery,this);



    // STLViewer Rendering Object
    function STLViewer(model, elementID) {
        var elem = document.getElementById(elementID);
        var camera = new THREE.PerspectiveCamera(70, 
            elem.clientWidth/elem.clientHeight, 1, 1000);
        var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(elem.clientWidth, elem.clientHeight);
        elem.appendChild(renderer.domElement);	

        var controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.rotateSpeed = 0.15;
        controls.dampingFactor = 0.05;
        controls.enableZoom = true;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 3;
        controls.mouseButtons.RIGHT = null;
        controls.touches.TWO = 3;

        var scene = new THREE.Scene();
        scene.add(new THREE.HemisphereLight(0xffffff, 1.5));

        function getGeometry(geometry) {
            geometry.rotateX(-Math.PI / 2);
            geometry.rotateY(Math.PI / 2);
            var modelColor = getComputedStyle(document.body).getPropertyValue('--basesub-color');
            modelColor = parseInt(modelColor.replace('#', '0x'), 16);
            var material = new THREE.MeshPhongMaterial({ 
                color: modelColor, 
                specular: 100, 
                shininess: 100 
            });
            var mesh = new THREE.Mesh(geometry, material);
            scene.add(mesh);
            
            var middle = new THREE.Vector3();
            geometry.computeBoundingBox();
            geometry.boundingBox.getCenter(middle);
            mesh.position.x = -1 * middle.x;
            mesh.position.y = -1 * middle.y;
            mesh.position.z = -1 * middle.z;
            var largestDimension = Math.max(geometry.boundingBox.max.x,
                                        geometry.boundingBox.max.y, 
                                        geometry.boundingBox.max.z)
            camera.position.z = largestDimension * 1.5;

            initCamX = camera.position.x 
            initCamY = camera.position.y 
            initCamZ = camera.position.z

            modelFlag = true;
            var animate = function () {
                if (modelFlag == true) {
                    requestAnimationFrame(animate);
                    controls.update();
                    renderer.render(scene, camera);
                }
                return ;
            }; 
            animate();


            function resizeListener(e) {
                renderer.setSize(elem.clientWidth, elem.clientHeight);
                camera.aspect = elem.clientWidth/elem.clientHeight;
                camera.updateProjectionMatrix();
            }
            
            window.addEventListener('resize', resizeListener, false);
            $("#model-wrapper").resize(resizeListener);

            function reload(){
                camera.position.x = initCamX
                camera.position.y = initCamY
                camera.position.z = initCamZ
            }
            
            $('#reset').on('click', reload);
        }
        
        (new THREE.STLLoader()).load(model, getGeometry);
    }


}

