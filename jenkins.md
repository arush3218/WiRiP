# WiRiP CI/CD with Jenkins on AWS EC2

Complete guide to deploy WiRiP with automated CI/CD using Jenkins on an EC2 free-tier instance.

---

## What You'll Build

- **Jenkins Server** on EC2 (automated builds & deployments)
- **GitHub Integration** (webhook triggers on push)
- **Automated Pipeline:**
  1. Pull latest code from GitHub
  2. Run tests (optional)
  3. Deploy to production
  4. Restart services
- **Production App** running alongside Jenkins

---

## Architecture

```
GitHub Push → Webhook → Jenkins → Build → Test → Deploy → Restart App
```

---

## Prerequisites

- AWS account
- GitHub repository (WiRiP already pushed)
- SSH key pair
- Basic Git/Linux knowledge

---

## Part 1: Launch EC2 Instance for Jenkins + App

### Step 1.1: Create EC2 Instance

1. **AWS Console** → EC2 → Launch Instance

2. **Configuration:**
   - **Name:** wirip-jenkins-server
   - **AMI:** Ubuntu Server 22.04 LTS (free tier)
   - **Instance Type:** t2.small or t2.medium (Jenkins needs more RAM; t2.micro may be slow)
     - ⚠️ **Note:** t2.small is NOT free tier but recommended ($0.023/hr ~$17/month)
     - For free tier only: use t2.micro but expect slower builds
   - **Key Pair:** Create/select and download .pem
   - **Network Settings:**
     - SSH (22) - Your IP only
     - HTTP (80) - 0.0.0.0/0
     - Custom TCP (8080) - 0.0.0.0/0 (Jenkins web UI)
   - **Storage:** 20 GB gp3 (Jenkins needs space for builds)

3. **Launch** and note **Public IP**

---

## Part 2: Install Java & Jenkins

### Step 2.1: Connect to EC2

```bash
ssh -i path/to/your-key.pem ubuntu@YOUR_EC2_IP
```

### Step 2.2: Update System

```bash
sudo apt update -y && sudo apt upgrade -y
```

### Step 2.3: Install Java (Jenkins requires Java 11 or 17)

```bash
sudo apt install -y openjdk-17-jdk
java -version
```

Expected output: `openjdk version "17.x.x"`

### Step 2.4: Install Jenkins

```bash
# Add Jenkins repo
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key

echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Install Jenkins
sudo apt update
sudo apt install -y jenkins

# Start Jenkins
sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo systemctl status jenkins
```

Look for "active (running)".

### Step 2.5: Get Jenkins Initial Password

```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

**Copy this password** - you'll need it in Step 3.

---

## Part 3: Configure Jenkins Web UI

### Step 3.1: Access Jenkins

Open browser: `http://YOUR_EC2_IP:8080`

### Step 3.2: Unlock Jenkins

- Paste the initial admin password from Step 2.5
- Click **Continue**

### Step 3.3: Install Plugins

- Select **Install suggested plugins**
- Wait for installation (2-5 minutes)

### Step 3.4: Create Admin User

- Username: `admin` (or your choice)
- Password: (strong password)
- Full name: Your name
- Email: your-email@example.com
- Click **Save and Continue**

### Step 3.5: Jenkins URL

- Keep default: `http://YOUR_EC2_IP:8080/`
- Click **Save and Finish**
- Click **Start using Jenkins**

---

## Part 4: Install Application Dependencies

Jenkins runs as `jenkins` user, so install Python/Nginx for the app.

### Step 4.1: Install App Dependencies

```bash
sudo apt install -y python3 python3-venv python3-pip git nginx
```

### Step 4.2: Give Jenkins User Permissions

```bash
# Add jenkins user to sudo group (for service restarts)
sudo usermod -aG sudo jenkins

# Allow jenkins to restart services without password
echo "jenkins ALL=(ALL) NOPASSWD: /bin/systemctl restart wirip, /bin/systemctl status wirip, /bin/systemctl daemon-reload" | sudo tee /etc/sudoers.d/jenkins
```

---

## Part 5: Set Up Application (Initial Manual Deploy)

### Step 5.1: Clone Repository

```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/wirip.git
sudo chown -R jenkins:jenkins wirip
cd wirip
```

### Step 5.2: Create Virtual Environment

```bash
sudo -u jenkins python3 -m venv venv
sudo -u jenkins /opt/wirip/venv/bin/pip install --upgrade pip
sudo -u jenkins /opt/wirip/venv/bin/pip install -r requirements.txt gunicorn
```

### Step 5.3: Create .env File

```bash
sudo -u jenkins nano /opt/wirip/.env
```

Paste (generate SECRET_KEY first):

```bash
# Generate key
python3 -c "import secrets; print(secrets.token_hex(32))"
```

```env
FLASK_ENV=production
SECRET_KEY=your-generated-key-here
DATABASE_URL=sqlite:///wirip.db
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 5.4: Initialize Database

```bash
sudo -u jenkins /opt/wirip/venv/bin/python /opt/wirip/app.py
```

Press `Ctrl+C` after "Database initialized".

### Step 5.5: Create Systemd Service

```bash
sudo nano /etc/systemd/system/wirip.service
```

```ini
[Unit]
Description=WiRiP Gunicorn Service
After=network.target

[Service]
User=jenkins
Group=www-data
WorkingDirectory=/opt/wirip
Environment="PATH=/opt/wirip/venv/bin"
EnvironmentFile=/opt/wirip/.env
ExecStart=/opt/wirip/venv/bin/gunicorn --workers 3 --bind unix:/opt/wirip/wirip.sock app:app
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable wirip
sudo systemctl start wirip
sudo systemctl status wirip
```

### Step 5.6: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/wirip
```

```nginx
server {
    listen 80;
    server_name _;

    location /static/ {
        alias /opt/wirip/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://unix:/opt/wirip/wirip.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/wirip /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

**Test:** Visit `http://YOUR_EC2_IP` - app should load!

---

## Part 6: Create Jenkins Pipeline

### Step 6.1: Install Git Plugin (if not installed)

1. Jenkins Dashboard → **Manage Jenkins** → **Plugins**
2. Search "Git Plugin" and install if needed

### Step 6.2: Create Pipeline Job

1. Jenkins Dashboard → **New Item**
2. Name: `wirip-deployment`
3. Select **Pipeline**
4. Click **OK**

### Step 6.3: Configure Pipeline

**General:**
- Description: "Automated deployment for WiRiP blog"

**Build Triggers:**
- ✅ Check **GitHub hook trigger for GITScm polling**

**Pipeline Section:**
- Definition: **Pipeline script**
- Script:

```groovy
pipeline {
    agent any
    
    environment {
        APP_DIR = '/opt/wirip'
        VENV_PYTHON = '/opt/wirip/venv/bin/python'
        VENV_PIP = '/opt/wirip/venv/bin/pip'
    }
    
    stages {
        stage('Pull Latest Code') {
            steps {
                echo 'Pulling latest code from GitHub...'
                dir("${APP_DIR}") {
                    sh 'git pull origin main'
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo 'Installing/updating Python packages...'
                dir("${APP_DIR}") {
                    sh "${VENV_PIP} install -r requirements.txt --upgrade"
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                echo 'Running tests...'
                dir("${APP_DIR}") {
                    // Add your test commands here
                    sh "${VENV_PYTHON} -m pytest || echo 'No tests configured yet'"
                }
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Restarting application...'
                sh 'sudo systemctl daemon-reload'
                sh 'sudo systemctl restart wirip'
                sh 'sudo systemctl status wirip'
            }
        }
    }
    
    post {
        success {
            echo '✅ Deployment successful!'
        }
        failure {
            echo '❌ Deployment failed. Check logs.'
        }
    }
}
```

Click **Save**

---

## Part 7: Set Up GitHub Webhook

### Step 7.1: Get Jenkins URL

Your Jenkins webhook URL:
```
http://YOUR_EC2_IP:8080/github-webhook/
```

### Step 7.2: Configure GitHub Webhook

1. Go to your GitHub repo: `https://github.com/YOUR_USERNAME/wirip`
2. Click **Settings** → **Webhooks** → **Add webhook**
3. **Payload URL:** `http://YOUR_EC2_IP:8080/github-webhook/`
4. **Content type:** `application/json`
5. **Which events:** Select **Just the push event**
6. ✅ Check **Active**
7. Click **Add webhook**

### Step 7.3: Test Webhook

GitHub will send a test ping. You should see a green checkmark ✅

---

## Part 8: Test the CI/CD Pipeline

### Step 8.1: Make a Change Locally

```powershell
# On your local machine
cd path\to\wirip
echo "# Test CI/CD" >> README.md
git add .
git commit -m "Test Jenkins CI/CD pipeline"
git push origin main
```

### Step 8.2: Watch Jenkins Build

1. Go to Jenkins: `http://YOUR_EC2_IP:8080`
2. Click **wirip-deployment** job
3. You should see a new build starting automatically!
4. Click the build number → **Console Output** to watch live logs

### Step 8.3: Verify Deployment

- Visit `http://YOUR_EC2_IP`
- App should be updated with latest changes

---

## Part 9: Advanced Configuration

### Option 1: Add Email Notifications

**Jenkins → Manage Jenkins → System → Email Notification:**
- SMTP server: `smtp.gmail.com`
- Use SMTP Authentication: ✅
- User Name: your-email@gmail.com
- Password: (app password)
- Use SSL: ✅
- SMTP Port: 465

**Update Jenkinsfile post section:**
```groovy
post {
    success {
        mail to: 'your-email@gmail.com',
             subject: "✅ WiRiP Deployed Successfully - Build #${env.BUILD_NUMBER}",
             body: "Deployment completed successfully!"
    }
    failure {
        mail to: 'your-email@gmail.com',
             subject: "❌ WiRiP Deployment Failed - Build #${env.BUILD_NUMBER}",
             body: "Check Jenkins logs: ${env.BUILD_URL}"
    }
}
```

### Option 2: Add Slack Notifications

1. Install "Slack Notification" plugin
2. Configure Slack workspace integration
3. Add to Jenkinsfile:

```groovy
post {
    success {
        slackSend color: 'good', message: "✅ WiRiP deployed successfully!"
    }
    failure {
        slackSend color: 'danger', message: "❌ WiRiP deployment failed!"
    }
}
```

### Option 3: Add Build Status Badge to README

Add to your `README.md`:
```markdown
![Build Status](http://YOUR_EC2_IP:8080/buildStatus/icon?job=wirip-deployment)
```

### Option 4: Run Tests with Coverage

Install pytest and coverage:
```bash
sudo -u jenkins /opt/wirip/venv/bin/pip install pytest pytest-cov
```

Update Jenkinsfile test stage:
```groovy
stage('Run Tests') {
    steps {
        dir("${APP_DIR}") {
            sh "${VENV_PYTHON} -m pytest --cov=. --cov-report=html tests/ || true"
        }
    }
}
```

---

## Part 10: Security Best Practices

### Step 10.1: Restrict Jenkins Access

**Add authentication:**
1. Jenkins → Manage Jenkins → Security
2. Enable **Jenkins' own user database**
3. Disable "Allow users to sign up"
4. Use **Matrix-based security**

### Step 10.2: Use SSH Keys for Git

```bash
# Generate SSH key for jenkins user
sudo -u jenkins ssh-keygen -t ed25519 -C "jenkins@wirip"

# Add to GitHub
sudo cat /var/lib/jenkins/.ssh/id_ed25519.pub
```

Add this public key to GitHub: Settings → SSH Keys

Update git remote in `/opt/wirip`:
```bash
cd /opt/wirip
sudo -u jenkins git remote set-url origin git@github.com:YOUR_USERNAME/wirip.git
```

### Step 10.3: Secure Jenkins with HTTPS

Use Let's Encrypt + Nginx as reverse proxy for Jenkins:

```bash
sudo nano /etc/nginx/sites-available/jenkins
```

```nginx
server {
    listen 80;
    server_name jenkins.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name jenkins.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/jenkins.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jenkins.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting

### Jenkins not starting?
```bash
sudo systemctl status jenkins
sudo journalctl -u jenkins -n 50
```

### Permission denied errors?
```bash
sudo chown -R jenkins:jenkins /opt/wirip
sudo chmod +x /opt/wirip/venv/bin/*
```

### Git pull fails in pipeline?
```bash
# Check git config
sudo -u jenkins git config --global --list

# Set git credentials
cd /opt/wirip
sudo -u jenkins git config credential.helper store
```

### App not restarting?
```bash
sudo systemctl status wirip
sudo journalctl -u wirip -n 50
```

### Webhook not triggering?
- Check GitHub webhook delivery history (Recent Deliveries)
- Ensure EC2 port 8080 is open in Security Group
- Jenkins URL must be accessible from internet

---

## Cost Optimization

**Free Tier (Limited):**
- t2.micro EC2 (slow but free for 12 months)
- Total: ~$0/month (first year)

**Recommended (Fast):**
- t2.small EC2 (~$17/month)
- Total: ~$17/month

**Alternative: Use GitHub Actions (Free for public repos)**
- 2,000 minutes/month free
- No EC2 cost for CI/CD

---

## Monitoring & Logs

**Jenkins Logs:**
```bash
sudo tail -f /var/log/jenkins/jenkins.log
```

**App Logs:**
```bash
sudo journalctl -u wirip -f
```

**Nginx Logs:**
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Next Steps

1. ✅ Add automated tests (pytest)
2. ✅ Set up staging environment
3. ✅ Add database backups to pipeline
4. ✅ Implement blue-green deployment
5. ✅ Add monitoring (Prometheus/Grafana)

---

## Summary

You now have:
- ✅ Jenkins CI/CD server on EC2
- ✅ Automated deployments on git push
- ✅ Production WiRiP app running
- ✅ GitHub webhook integration
- ✅ Systemd auto-restart
- ✅ Nginx reverse proxy

**Every git push to main → Auto-deploys to EC2!** 🚀

---

**Questions? Check Jenkins console output or GitHub Issues.**
