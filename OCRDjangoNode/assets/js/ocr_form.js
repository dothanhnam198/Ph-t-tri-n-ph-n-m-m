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
$(document).ready(function() {
    var $imageInput = $("[data-js-image-input]");
    var $imageContainer = $("[data-js-image-container]");
    var $resultContainer = $("[data-js-result-container]");
    var imagepdfSelectChange = function(event) {
            event.stopPropagation();
            event.preventDefault();
            var file = event.target.files[0];

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

                };
            })(file);
            fileReader.readAsDataURL(file);
        }
    $imageInput.change(imagepdfSelectChange);
    $("[data-js-add-button]").click(function(event) {
        event.stopPropagation();
        event.preventDefault();
        var lastChild = $('.input-file-container').children().last();
        var $imageInput=$(lastChild[0].outerHTML);
        $imageInput.appendTo($('.input-file-container'))
        var $imageContainer = $("[data-js-image-container]");
        var $resultContainer = $("[data-js-result-container]");
        $imageInput.change(imagepdfSelectChange);
    });
    $("[data-js-go-button]").click(function(event) {
        event.stopPropagation();
        event.preventDefault();

        var $imageInput = $("[data-js-image-input]");
        $resultContainer.html('');
        start = performance.now();
        $(".loading").show();

debugger
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
        for(var  i=0;i<$imageInput.length;i++) {
            inputOCR.images.push($($imageInput[i].files[0]).attr('data'));
            inputOCR.image_names.push($($imageInput[i].files[0]).attr('fname'));
        }
        inputOCR.templates=[];
        var $coordInput = $("[data-js-template-input]");
        inputOCR.templates=(JSON.parse('['+$coordInput.text()+']'));

        inputOCR.file_input=$("[data-js-file-input-input]").val();
        inputOCR.file_output=$("[data-js-file-output-input]").val();
        inputOCR.ftp_ip=$("[data-js-ftp-ip-input]").val();
        inputOCR.ftp_port=$("[data-js-ftp-port-input]").val();
        inputOCR.ftp_user=$("[data-js-ftp-user-input]").val();
        inputOCR.ftp_pwd=$("[data-js-ftp-pwd-input]").val();
        inputOCR.client_folder=$("[data-js-ftp-folder-input]").val();

        data = new FormData();
        data.append('inputOCR', JSON.stringify(inputOCR));
        $.post({
            url: "/ocr/",
            data: data,
            cache: false,
            contentType: false,
            processData: false
        }).done(function(data) {
            console.log(data);
            $resultContainer.removeClass("result-default result-error");
            $resultContainer.addClass("result-success");
            sResult=data.timeexecute
            debugger

            if(data.status!='OK')
                sResult+='<br>'+''+data.status

            $.grep(data.results, function(fileout,i){
                fileout=JSON.parse(fileout)
                window.result=fileout
                sResult+='<br>'+'File '+i+', '+fileout.filename+':'
                if(fileout.output_pdf)
                    sResult+='<br>'+'<a download=pdfTitle href="data:application/pdf;base64,'+fileout.output_pdf+'" title="Download pdf document" >Download PDF</a>'
                if(fileout.output_text)
                    sResult+='<br>'+'<a download=text href="data:application/octet-stream,'+fileout.output_text+'" title="Download text document" >Download TEXT</a>'
                if(fileout.output_json)
                    sResult+='<br>'+'<a download=text href="data:application/octet-stream,'+fileout.output_json+'" title="Download text document" >Download JSON from template</a>'

                $.grep(fileout.output_pages, function(pageout,i2){
                    sResult+='<br>'+'Page '+i2+':'+(pageout.page_number)
                    sResult+='<br>'+'<div class="box-parent" style="position:sticky;"><img style="opacity:0.2;" src="data:image/png;base64,'+pageout.page_image+'">'

                    sResult+=''
                    if((pageout.page_json+'').trim()!='' && (pageout.page_json+'').trim()!='[]') {
                        $.grep(JSON.parse((pageout.page_json+"").replace(/'/g, '"')), function(boxstr,i3){
                            var box = boxstr
                            if(box.box==0)
                                sResult+='<div class="box" style="position:absolute;border:1px solid gray;top:'+box.top+'px;left:'+box.left+'px;width:'+box.width+'px;height:'+box.height+'px;"><span contentEditable1="true">'+''+(box.text)+'</span>'+'-'+box.angle+'</div>'
                        });
                    }

                    sResult+='</div>'

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
