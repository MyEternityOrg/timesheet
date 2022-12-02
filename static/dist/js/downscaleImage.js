function downscaleImage(dataUrl, newWidth, imageType, imageArguments) {
    "use strict";
    var image, oldWidth, oldHeight, newHeight, canvas, ctx, newDataUrl;

    // Provide default values
    imageType = "image/jpeg";
    imageArguments = 0.3;

    // Create a temporary image so that we can compute the height of the downscaled image.
    image = new Image();
    image.src = dataUrl;
    // newHeight = Math.floor(oldHeight / oldWidth * newWidth)
    newHeight = Math.floor(newWidth*1.2)

    // Create a temporary canvas to draw the downscaled image on.
    canvas = document.createElement("canvas");
    canvas.width = newWidth;
    canvas.height = newHeight;
    var ctx = canvas.getContext("2d");

    // Draw the downscaled image on the canvas and return the new data URL.
    ctx.drawImage(image, 0, 0, newWidth, newHeight);
    newDataUrl = canvas.toDataURL(imageType, imageArguments);
    return newDataUrl;
}

function scaleImage(file, clientWidth, clientHeight) {

    let image = new Image();
    image.src = window.URL.createObjectURL(file);
    console.log(image.src);
    let canvas = document.createElement("canvas");
    let ctx = canvas.getContext("2d");
    ctx.drawImage(image, 0, 0, clientWidth, clientHeight);
    let new_src = canvas.toDataURL("image/jpeg");
    console.log(new_src);
    return new_src;
}


function uploaderImage() {
    // 1.
    const canvas =  document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // 2.
    const reader = new FileReader();
    const img = document.getElementById("imgScaled");

    // 3.
    const uploadImage = (e) => {
        reader.onload = () => {
            img.onload = () => {
                // canvas.width = img.width/100;
                // canvas.height = img.height/100;
                ctx.drawImage(img, 0, 0, 100, 150);
            };
            img.src = reader.result;
            console.log(reader.result);
        };
        reader.readAsDataURL(e.target.files[0]);
    };

    // 4.
    const imageLoader = document.getElementById("photo");
    imageLoader.addEventListener("change", uploadImage);
};