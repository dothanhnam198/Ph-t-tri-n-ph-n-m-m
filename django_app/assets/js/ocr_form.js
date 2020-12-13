var api_url = 'http://14.248.83.163:9654/'

function showCoords(c)
{
    //Jcrop
    var $coordInput = $("[data-js-template-input]");
    s=('{"x":'+ c.x +', "y":'+ c.y +', "x2":'+ c.x2 +', "y2":'+ c.y2);
    s+=(', "w":'+c.w +', "h":'+ c.h+'}');
    $coordInput.text(s);
};
function debugQtyAreas (event, id, areas) {
	console.log(areas.length + " areas", arguments);

    var $imageContainer = $("[data-js-image-container]");
	var areas = $($imageContainer.find('img')).selectAreas('areas');
	displayAreas(areas, $($imageContainer.find('img')));
};
function displayAreas (areas, image) {
    var text = "";
    $.each(areas, function (id, area) {
        text += (text==''?'':', ')+'{'+areaToString(area, image)+'}';
    });
    var $coordInput = $("[data-js-template-input]");
    $coordInput.text(text);
};
function areaToString (area, image) {
    //return (typeof area.id === "undefined" ? "" : (area.id + ": ")) + area.x + ':' + area.y  + ' ' + area.width + 'x' + area.height + '<br />'
    ratio = 1 / (image.width() / image.attr('realw'));
    return (typeof area.id === "undefined") ? "" : ('"x":'+area.x.toFixed(2) + ', "y":' + area.y.toFixed(2)  + ', "w":' + area.width.toFixed(2) + ', "h":' + area.height.toFixed(2) + ', "r":'+ratio.toFixed(5)+', "title":"'+area.title+'", "description":"'+area.description+'" ')
}
function uploadTrunkFile(ifile, folder) {
    var $imageInput = $("[data-js-image-input]");
    var file = $imageInput[ifile].files[0];
    inputFile = {};
    inputFile.folder = folder;
    inputFile.filename = $(file).attr('fname');
    inputFile.size = file.size;
    var data = new FormData();
    data.append('inputFile', JSON.stringify(inputFile));
    $.post({
        url: api_url+"api/?cmd=uploadstart",
        data: data,
        cache: false,
        contentType: false,
        processData: false
    }).done(function(data) {
        var trunk = 2*1024*1024;
        var totalTrunk = file.size / trunk + 1;
        for(var i=0;i<totalTrunk;i++) {
            var opt_startByte = i*trunk
            var opt_stopByte = (i+1)*trunk

            var start = parseInt(opt_startByte) || 0;
            var stop = parseInt(opt_stopByte) || file.size - 1;

            // If we use onloadend, we need to check the readyState.
            var reader = new FileReader();

            reader.filename = $(file).attr('fname');
            reader.trunkno = i;
            reader.trunkstart = start;
            reader.fileno = ifile;
            reader.folder = folder;
            reader.size = file.size;
            // If we use onloadend, we need to check the readyState.
            reader.onloadend = function(evt) {
              if (evt.target.readyState == FileReader.DONE) { // DONE == 2

            window.yy=evt

                inputFile = {};
                inputFile.filename = evt.target.filename;
                inputFile.folder = evt.target.folder;
                inputFile.trunkno = evt.target.trunkno;
                inputFile.trunkstart = evt.target.trunkstart;
                inputFile.size = evt.target.size;
                inputFile.trunk = btoa(evt.target.result);
                if(evt.target.result.length > 0) {
                    var data = new FormData();
                    data.append('inputFile', JSON.stringify(inputFile));
                    $.post({
                        url: api_url+"api/?cmd=uploadtrunk",
                        data: data,
                        cache: false,
                        contentType: false,
                        processData: false
                    }).done(function(data) {
                        var $imageInput = $("[data-js-image-input]");
                        console.log($imageInput[ifile].files[0])
                        console.log('$imageInput[ifile]')
                        $($imageInput[ifile].files[0]).attr('data','');
                        if($($imageInput[ifile]).attr('title')=='')
                            $($imageInput[ifile]).attr('title', 'Uploaded trunk no ')
                        $($imageInput[ifile]).attr('title',$($imageInput[ifile]).attr('title')+', '+data.trunkno);
                        $($imageInput[ifile]).attr('data-original-title', $($imageInput[ifile]).attr('title'))
                        $($imageInput[ifile]).tooltip('show');
                        setTimeout(function () {
                            $($imageInput[ifile]).tooltip('hide');
                          }, 5000);
                    }).fail(function(jqXHR) {
                        window.xx=jqXHR;
                        console.log(jqXHR);
                        alert('Loi')
                    });
                }
              }
            };

            var blob = file.slice(start, stop + 1);
            reader.readAsBinaryString(blob);
        }
    }).fail(function(jqXHR) {
        console.log(jqXHR);
        alert('Loi')
    });
}

$(document).ready(function() {
    var $imageInput = $("[data-js-image-input]");
    var $imageContainer = $("[data-js-image-container]");
    var $resultContainer = $("[data-js-result-container]");
    $.grep($imageInput, function(e, i) { $(e).attr('fileno', i) });
    var imagepdfSelectChange = function(event) {
            event.stopPropagation();
            event.preventDefault();
            var file = event.target.files[0];
            var fileinput = event.target;

            var fileReader = new FileReader();
            fileReader.onload = (function(theFile) {
                return function(event) {
                    $(file).attr('data', event.target.result);
                    $(file).attr('fname', theFile.name);

                    $imageContainer.html('');
                    $resultContainer.html('');
                    var image = new Image();
                    image.onload = function (evt) {
                        var width = this.width;
                        var height = this.height;

                        $imageContainer.html('<img class="image" realw="'+width+'" realh="'+height+'" src="' + event.target.result + '">');

                        $($imageContainer.find('img')).selectAreas({
                            minSize: [10, 10],
                            onChanged: debugQtyAreas,
                            //width: 500,
                            areas: [
                            ]
                        });
                    };
                    image.src = event.target.result;
                    //$($imageContainer).append(image);
                    //tu dong upload
                    uploadTrunkFile($(fileinput).attr('fileno'), $("[data-js-temp-folder-input]").val())
                };
            })(file);
            fileReader.readAsDataURL(file);
        }
    $imageInput.change(imagepdfSelectChange);
    $("[data-js-upload-button]").click(function(){
        var $imageInput = $("[data-js-image-input]");
        for(var  i=0;i<$imageInput.length;i++) {
            if($imageInput[i].files[0]) {
                uploadTrunkFile(i, $("[data-js-temp-folder-input]").val())
            }
        }
    });
    $.get({
            url: api_url+"api/?cmd=get_ftp",
            cache: false,
            contentType: false,
            processData: false
        }).done(function(data) {
            //$("[data-js-ftp-ip-input]").val(data.ftp_ip);
            //$("[data-js-ftp-port-input]").val(data.ftp_port);
            //$("[data-js-ftp-user-input]").val(data.ftp_user);
            //$("[data-js-ftp-pwd-input]").val(data.ftp_pwd);
            //$("[data-js-ftp-folder-input]").val(data.client_folder);
            $("[data-js-temp-folder-input]").val(data.client_folder);
        }).fail(function(jqXHR) {
            window.xx=jqXHR;
            console.log(jqXHR);
            alert('Loi')
        });
    $("[data-js-add-button]").click(function(event) {
        event.stopPropagation();
        event.preventDefault();
        var lastChild = $('.input-file-container').children().last();
        var $imageInput=$(lastChild[0].outerHTML);
        $imageInput.appendTo($('.input-file-container'))
        var $imageContainer = $("[data-js-image-container]");
        var $resultContainer = $("[data-js-result-container]");
        $imageInput.change(imagepdfSelectChange);
        var $imageInput = $("[data-js-image-input]");
        $.grep($imageInput, function(e, i) { $(e).attr('fileno', i) });
    })
    $("[data-js-go-button]").click(function(event) {
        event.stopPropagation();
        event.preventDefault();

        var $imageInput = $("[data-js-image-input]");
        $resultContainer.html('');
        start = performance.now();
        $(".loading").show();

        inputOCR = {}
        inputOCR.lang=$("[data-js-lang-input]").val();
        inputOCR.PSM=$("[data-js-psm-input]").val();
        inputOCR.OEM=$("[data-js-oem-input]").val();
        inputOCR.spelling=$("[data-js-spell-input]").val();
        inputOCR.deskew='';
        if($("[data-js-check-deskew-input]").prop('checked'))
            inputOCR.deskew='1';
        inputOCR.remove_background='';
        if($("[data-js-check-remove-background-input]").prop('checked'))
            inputOCR.remove_background='1';
        inputOCR.clean='';
        if($("[data-js-check-clean-input]").prop('checked'))
            inputOCR.clean='1';
        inputOCR.clean_final='';
        if($("[data-js-check-clean-final-input]").prop('checked'))
            inputOCR.clean_final='1';

        inputOCR.output_type='';
        if($("[data-js-check-out-pdf-input]").prop('checked'))
            inputOCR.output_type+=',PDF';
        if($("[data-js-check-out-text-input]").prop('checked'))
            inputOCR.output_type+=',TEXT';
        if($("[data-js-check-out-page-input]").prop('checked'))
            inputOCR.output_type+=',PAGE';

        inputOCR.page_number=$("[data-js-page-input]").val();
        inputOCR.api_callback=$("[data-js-api-callback-input]").val();

        inputOCR.images=[];
        inputOCR.image_names=[];
        inputOCR.file_input=[];
        inputOCR.file_output=[];
        for(var  i=0;i<$imageInput.length;i++) {
            if($imageInput[i].files[0]) {
                if($($imageInput[i].files[0]).attr('data')+''!='')
                    inputOCR.images.push($($imageInput[i].files[0]).attr('data'));
                    inputOCR.image_names.push($($imageInput[i].files[0]).attr('fname'));

                inputOCR.file_input.push($($imageInput[i].files[0]).attr('fname'));
                inputOCR.file_output.push($($imageInput[i].files[0]).attr('fname')+'output.pdf');
            }
        }

        inputOCR.templates=[];
        var $coordInput = $("[data-js-template-input]");
        inputOCR.templates=(JSON.parse('['+$coordInput.text()+']'));

        inputOCR.ftp_ip=$("[data-js-ftp-ip-input]").val();
        inputOCR.ftp_port=$("[data-js-ftp-port-input]").val();
        inputOCR.ftp_user=$("[data-js-ftp-user-input]").val();
        inputOCR.ftp_pwd=$("[data-js-ftp-pwd-input]").val();
        inputOCR.client_folder=$("[data-js-ftp-folder-input]").val();
        inputOCR.temp_ocr_folder=$("[data-js-temp-folder-input]").val();

        data = new FormData();
        data.append('inputOCR', JSON.stringify(inputOCR));
        console.log(inputOCR)
        $.post({
            url: api_url+"ocr/",
            data: data,
            cache: false,
            contentType: false,
            processData: false
        }).done(function(data) {
            console.log(JSON.parse(data.results[0]));
            $resultContainer.removeClass("result-default result-error");
            $resultContainer.addClass("result-success");
            sResult=data.timeexecute

            if(data.status!='OK')
                sResult+='<br>'+''+data.status

            $.grep(data.results, function(fileout,i){
                fileout=JSON.parse(fileout)
                window.result=fileout
                sResult+='<br>'+'File '+fileout.file_number+', '+fileout.file_input+':<table>'
                $.grep(fileout.result_files, function(fileout2,i2){
                console.log(fileout2)
                    sResult+='<tr><td>'+'<a download=pdfTitle href="'+fileout2.file_link+'" title="Download '+fileout2.file_type+' document" >'+fileout2.file_name+'</a></td></tr>'
                    $.grep(fileout2.result_pages, function(pageout,i2){
                        sResult+='<tr><td>'+'Page '+(pageout.page_number)+':</td></tr>'
                        $.grep(pageout.page_files, function(pageoutocr,i3){
                            sResult+='<tr><td>'+'<a download=pdfTitle href="'+pageoutocr.file_link+'" title="Download '+pageoutocr.file_type+' document" >'+pageoutocr.file_name+'</a></td></tr>'

                            //sResult+='<br>'+'<div class="box-parent" style="position:sticky;"><img style="opacity:0.2;" src="data:image/png;base64,'+pageout.page_image+'">'
                        });
                    });
                });
                console.log(fileout)
            })
            console.log(data)
            $resultContainer.html(sResult);

            var index_letters_resize;
            index_letters_resize = function() {
              $(".box").each(function() {
                var
                  $this = $(this),
                  height = Math.min( Math.max( parseInt( $this.height() ), 4 ), 150 );
                $this.css({
                  fontSize: height
                });
              });
            }
            //index_letters_resize();
            shrinkTextInElement = function(el, minFontSizePx) {
                if(!minFontSizePx) {
                    minFontSizePx = 5;
                }
                while(el.offsetWidth > el.parentNode.offsetWidth || el.offsetHeight > el.parentNode.offsetHeight) {

                    var newFontSize = (parseInt(el.style.fontSize, 10) - 1);
                    if(newFontSize <= minFontSizePx) {
                        break;
                    }
                    el.style.fontSize = newFontSize + "px";
                }
            }

            $.grep($('.box span'), function(box,i2){
                box.style.fontSize = 100 + "px";
                shrinkTextInElement(box, 1);
            });
            $(".loading").hide();
        })
        .fail(function(jqXHR) {
            $resultContainer.removeClass("result-default result-success");
            $resultContainer.addClass("result-error");
            $resultContainer.html('I AM ERROR');
            $(".loading").hide();
        });
    });

    i = 0;
    var start = performance.now();
    setInterval(function() {
      i = ++i % 4;
      duration = (performance.now() - start);
      $(".loading").text("Processing OCR " + Array(i+1).join(".") + " in " + parseInt(duration/1000) + "s");
    }, 800);
    $(".loading").hide();

});
