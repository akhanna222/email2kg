# Gmail OAuth Production Setup Guide

This guide explains how to make Email2KG available to **any Gmail user** (not just test users) in production.

## Current Status: Testing Mode

By default, Google OAuth applications start in **"Testing" mode**, which:
- ❌ Only allows up to 100 test users
- ❌ Requires manually adding each user's email to test users list
- ❌ Not suitable for public applications
- ✅ Good for development and limited beta testing

## Goal: Production Mode

To allow **any Gmail user** to connect, you need to:
1. ✅ Complete OAuth Consent Screen
2. ✅ Submit app for Google verification
3. ✅ Get approved by Google
4. ✅ Publish app to "Production" status

---

## Option 1: Quick Start (Internal/Limited Users)

If you want to **test with up to 100 users** without full verification:

### Steps:

1. **Keep "Testing" Mode:**
   - Your app stays in Testing mode
   - You can add up to 100 test users
   - Good for internal teams, beta testers, or small user bases

2. **Add Test Users:**
   ```
   Google Cloud Console → APIs & Services → OAuth consent screen
   → Test users → Add Users
   → Enter email addresses
   ```

3. **User Experience:**
   - Users see "This app isn't verified" warning
   - They can click "Advanced" → "Go to Email2KG (unsafe)" to proceed
   - Works but not ideal for end users

**Pros:**
- ✅ Quick setup (5 minutes)
- ✅ No verification needed
- ✅ Up to 100 users

**Cons:**
- ❌ Must manually add each user
- ❌ "Unverified app" warning scares users
- ❌ Limited to 100 users

---

## Option 2: Full Production (Any Gmail User)

For a **public production app** accessible to any Gmail user:

### Phase 1: Complete OAuth Consent Screen

1. **Go to Google Cloud Console:**
   ```
   https://console.cloud.google.com/
   → Select your project
   → APIs & Services → OAuth consent screen
   ```

2. **Choose User Type:**
   - Select **"External"** (for public users)
   - Internal is only for Google Workspace organizations

3. **Fill App Information:**
   ```
   App name: Email2KG
   User support email: your-support@email.com
   App logo: (upload a 120x120px logo)
   Application home page: https://agenticrag360.com
   Application privacy policy: https://agenticrag360.com/privacy
   Application terms of service: https://agenticrag360.com/terms
   Authorized domains: agenticrag360.com
   Developer contact: your-email@example.com
   ```

4. **Configure Scopes:**
   - Click "Add or Remove Scopes"
   - Add these Gmail scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/userinfo.email
     https://www.googleapis.com/auth/userinfo.profile
     ```
   - Save

5. **Save and Continue**

### Phase 2: Create Required Legal Pages

Google **requires** these pages for verification:

#### 1. **Privacy Policy** (required)

Create `/frontend/public/privacy.html` or add to your site:

Key sections needed:
- What data you collect (email content, user profile)
- How you use it (AI processing, knowledge graph)
- How you store it (encrypted database)
- How users can delete their data
- Third-party services (OpenAI for processing)

Example template: https://www.termsfeed.com/privacy-policy-generator/

#### 2. **Terms of Service** (required)

Create `/frontend/public/terms.html` or add to your site:

Key sections:
- Service description
- User responsibilities
- Acceptable use policy
- Liability limitations
- Account termination

Example template: https://www.termsfeed.com/terms-service-generator/

#### 3. **Support/Contact Page** (required)

Simple contact form or support email page.

### Phase 3: Submit for Verification

1. **Prepare for Review:**
   - ✅ App fully functional at production URL
   - ✅ Privacy policy published
   - ✅ Terms of service published
   - ✅ Support page available
   - ✅ App logo ready
   - ✅ OAuth consent screen complete

2. **Submit Application:**
   ```
   Google Cloud Console
   → OAuth consent screen
   → Click "Prepare for verification"
   → Fill out verification form
   ```

3. **Verification Form Details:**

   **App Domain Verification:**
   - Prove you own agenticrag360.com
   - Add Google verification meta tag to your site
   - Or add TXT record to DNS

   **OAuth Justification:**
   - Explain why you need Gmail readonly access
   - Describe your app functionality
   - Provide demo video (optional but helpful)

   **Brand Verification:**
   - Upload brand logo
   - Confirm brand name
   - Provide official links

4. **Submit Video Demo:**
   - Record 5-minute screencast showing:
     - User signs up
     - User connects Gmail via OAuth
     - App reads emails and extracts data
     - User views results
   - Upload to YouTube (unlisted)
   - Include link in verification form

### Phase 4: Wait for Approval

**Timeline:**
- **Initial Review:** 1-2 weeks
- **Additional Info Requests:** May ask for clarifications
- **Total Time:** 2-8 weeks typically

**Google Will Check:**
- ✅ Privacy policy compliance
- ✅ Terms of service adequacy
- ✅ App security (HTTPS required)
- ✅ Scope justification (why you need Gmail access)
- ✅ Brand consistency
- ✅ User data handling

### Phase 5: Publish to Production

Once approved:

1. **Change to Production:**
   ```
   OAuth consent screen → Publishing status
   → Click "Publish App"
   ```

2. **Update Your App:**
   - No code changes needed
   - Existing OAuth credentials work in production
   - Remove test user restrictions

3. **Result:**
   - ✅ Any Gmail user can connect
   - ✅ No "unverified app" warning
   - ✅ Professional user experience
   - ✅ Unlimited users

---

## Option 3: Alternative Approaches

### A. Use Organization Workspace (Internal Users Only)

If you have Google Workspace:
- Choose "Internal" user type
- Only users in your organization can use it
- No verification needed
- Good for company-internal tools

### B. Request Sensitive Scope Exemption

For trusted partners or specific use cases:
- Apply for exemption from some verification requirements
- Requires business relationship with Google
- Rarely approved

### C. Use Service Account (Different Use Case)

If you're accessing YOUR OWN Gmail (not user's):
- Use Google Service Account
- No OAuth consent screen needed
- Users don't connect their Gmail
- Not suitable for your use case

---

## Technical Requirements for Production

### 1. HTTPS Required

✅ **Already set up** via Let's Encrypt

```bash
# Your current setup
https://agenticrag360.com  # ✓ Valid SSL
```

### 2. Verified Domain

✅ **Already configured**

```bash
# Domain ownership proven through:
- SSL certificate for agenticrag360.com
- DNS A record pointing to your server
```

### 3. Secure OAuth Flow

✅ **Already implemented**

```javascript
// Your current OAuth setup
GOOGLE_REDIRECT_URI=https://agenticrag360.com/api/auth/google/callback
```

### 4. Data Privacy Compliance

**Required Updates:**

1. **Add Privacy Policy Page:**
   ```bash
   # Create frontend/public/privacy.html
   # Or add route to serve privacy policy
   ```

2. **Add Terms of Service:**
   ```bash
   # Create frontend/public/terms.html
   ```

3. **Add User Data Deletion:**
   ```python
   # backend/app/routers/auth.py
   @router.delete("/account")
   async def delete_account(current_user: User):
       # Delete all user data
       # Required by GDPR and Google policies
   ```

4. **Implement Data Export:**
   ```python
   @router.get("/export-data")
   async def export_user_data(current_user: User):
       # Return all user data as JSON/CSV
   ```

---

## Recommended Path

For **public production** (any Gmail user):

1. **Week 1:** Create privacy policy and terms pages
2. **Week 2:** Complete OAuth consent screen fully
3. **Week 3:** Record demo video and submit for verification
4. **Weeks 4-10:** Wait for Google review, respond to questions
5. **Week 10+:** Get approved and publish

For **limited beta** (up to 100 users):

1. **Today:** Stay in Testing mode
2. **Add test users** as they sign up
3. **Users click through** "unverified app" warning
4. **Works immediately** but not ideal UX

---

## Cost Considerations

**Google OAuth:**
- ✅ **Free** for basic Gmail API access
- ✅ No ongoing fees
- ✅ No per-user costs

**Only Required:**
- Domain name ($10-15/year) ✅ Already have
- SSL certificate (Free with Let's Encrypt) ✅ Already setup
- Time for verification process (2-8 weeks)

---

## FAQ

### Q: Can I use it in production before verification?

**A:** Yes, in "Testing" mode with up to 100 test users. They'll see an "unverified app" warning but can proceed.

### Q: How long does verification take?

**A:** Typically 2-8 weeks. Google may request additional information or clarifications.

### Q: Will my existing OAuth credentials still work?

**A:** Yes! Same credentials work in both Testing and Production modes.

### Q: Do I need a business entity?

**A:** No, individuals can get verified. However, having a registered business may help.

### Q: Can I get rejected?

**A:** Yes, if:
- Privacy policy is inadequate
- App security issues
- Unclear scope justification
- Missing required pages

But you can resubmit after fixing issues.

### Q: What if I just want 10-20 beta users?

**A:** Stay in Testing mode. Add their emails to test users list. Much faster than full verification.

---

## Next Steps

**Choose your path:**

### Path A: Quick Beta (Recommended to Start)
1. Keep Testing mode
2. Add beta users manually
3. Launch quickly
4. Submit for verification later

### Path B: Full Production
1. Create privacy policy & terms
2. Complete consent screen
3. Record demo video
4. Submit for verification
5. Wait 2-8 weeks

**My Recommendation:**
Start with **Path A** (Testing mode) to get users and feedback quickly, then submit for verification (Path B) once you have traction and can create polished legal pages.

---

## Support

If you need help:
- Google OAuth Support: https://support.google.com/cloud/answer/9110914
- Verification Help: https://support.google.com/cloud/answer/9110914
- API Console: https://console.cloud.google.com/

---

**Last Updated:** December 2024
**Author:** Email2KG Team
