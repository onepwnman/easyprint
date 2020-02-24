// Message Flashing  
PNotify.defaults.styling = 'bootstrap4';
PNotify.defaults.icons = 'fontawesome4';  

function notification(type, title, text, icon){
    var note = PNotify.alert({
        type: type,
        title: title,
        text: text,
        icon: icon,
        width: "350px"
    });

    note.on('click', function(){
        note.close();
    });
}


