shouldPrint();
//replacePrintButton();
var element;
var imgElemente;

async function replacePrintButton(){
    while (true) {
        console.log("running...");
        element = document.querySelector('[data-security-keys="Employees_Employee_PersonnelFile_DocumentPreview_PrintCopy"]');

        if (element) {
            var gefunden = element;
            var elementOhneEvents = removeAllEventListeners(element);

            console.log("Das Element wurde gefunden:", elementOhneEvents);

            link = false;
            imgElemente = document.querySelectorAll('img');
            for (var i = 0; i < imgElemente.length; i++) {
                var image = imgElemente[i];
                if (image.src.includes("/hrportalapi/DMS/DocumentPreview")) {
                    console.log("Das gewuenschte img-Element wurde gefunden:", image);
                    elementOhneEvents.addEventListener('click', function() {
                        location.href = image.src;
                    });
                    break;
                }
            }
        } else {
            console.log("Das Element wurde nicht gefunden, oder bereits editiert");
        }
        await sleep(1000);
    }
}


async function shouldPrint() {
    await sleep(500);

    var bodyElement = document.querySelector('body');
    bodyElement.style.backgroundColor = 'white';

    var imgElemente = document.querySelectorAll('body img');
    if (imgElemente.length === 1 && document.body.children.length === 1) {
        var imgElement = document.querySelector('img');
        imgElement.style.width = imgElement.naturalWidth + 'px';
        imgElement.style.height = imgElement.naturalHeight + 'px';
        print();
    }
}

function removeAllEventListeners(element) {
    var clone = element.cloneNode(true);
    if (element.parentNode) {
        element.parentNode.replaceChild(clone, element);
    }
    return clone;
}

//Sleep Function
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
