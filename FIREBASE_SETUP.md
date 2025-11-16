# Firebase Setup Guide

## Firebase Project Information
- **Project ID**: intellisynth-c1050
- **Auth Domain**: intellisynth-c1050.firebaseapp.com
- **Storage Bucket**: intellisynth-c1050.firebasestorage.app

## Getting Service Account Credentials

To use Firebase Admin SDK on the backend, you need to generate a service account key:

### Step 1: Go to Firebase Console
1. Visit: https://console.firebase.google.com/project/intellisynth-c1050/settings/serviceaccounts/adminsdk
2. Or navigate: Firebase Console → Project Settings → Service Accounts

### Step 2: Generate New Private Key
1. Click **"Generate new private key"**
2. Confirm by clicking **"Generate key"**
3. A JSON file will be downloaded (e.g., `intellisynth-c1050-firebase-adminsdk-xxxxx.json`)

### Step 3: Save the Credentials File
1. Rename the downloaded file to: `firebase-credentials.json`
2. Move it to your project root directory:
   ```
   C:\Users\akonr\Documents\code\ai_flight_recorder_backend_with_db\firebase-credentials.json
   ```

### Step 4: Secure the File
**IMPORTANT**: Add to `.gitignore` to prevent committing credentials:
```
firebase-credentials.json
```

## Alternative: Environment Variables

Instead of using a JSON file, you can set these environment variables:

```env
FIREBASE_PROJECT_ID=intellisynth-c1050
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour_Private_Key_Here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@intellisynth-c1050.iam.gserviceaccount.com
```

## Firestore Database Setup

### Enable Firestore
1. Go to: https://console.firebase.google.com/project/intellisynth-c1050/firestore
2. Click **"Create database"**
3. Choose **Production mode** or **Test mode**
   - **Production mode**: Requires security rules (recommended)
   - **Test mode**: Open access for 30 days (easier for development)
4. Select a location (e.g., `us-central1`)
5. Click **"Enable"**

## Testing the Connection

After setting up credentials, test the connection:

```bash
# Create a test script
python -c "from app.firebase_config import firebase_config; print('✓ Connected!' if firebase_config.initialize() else '✗ Failed')"
```

## Current Configuration

The app is configured to use:
- **SQLite** by default (for local development)
- **Firebase** when `DATABASE_TYPE=firebase` in environment

To switch to Firebase:
```env
DATABASE_TYPE=firebase
FIREBASE_CREDENTIALS=./firebase-credentials.json
```

## Security Notes

⚠️ **Never commit these files:**
- `firebase-credentials.json`
- `.env` (if it contains real credentials)

✅ **Safe to commit:**
- `.env.example` (template with placeholder values)
- `FIREBASE_SETUP.md` (this guide)

## Next Steps

1. Download service account key (see Step 2 above)
2. Save as `firebase-credentials.json` in project root
3. Enable Firestore database
4. Update `.env` file with `DATABASE_TYPE=firebase`
5. Run the server and test!
