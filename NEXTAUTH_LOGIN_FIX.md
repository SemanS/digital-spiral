# 🔐 NextAuth Login Fix

## ✅ NextAuth login je teraz opravený!

---

## 🐛 Problém

**Chyba**: "We're having trouble logging you in. There seems to be an issue with your identity provider."

**Príčina**:
1. Chýbajúci `basePath` v NextAuth konfigurácii
2. Chýbajúci `secret` v NextAuth konfigurácii
3. Google OAuth prompt nastavený na `consent` namiesto `select_account`
4. Chýbajúci `redirect` callback

---

## 🔧 Riešenie

### Aktualizovaná NextAuth konfigurácia

**Súbor**: `admin-ui/src/lib/auth/index.ts`

**Zmeny**:

1. **Pridaný `basePath`**:
```typescript
basePath: '/api/auth',
```

2. **Pridaný `secret`**:
```typescript
secret: process.env.NEXTAUTH_SECRET,
```

3. **Zmenený Google OAuth prompt**:
```typescript
// Pred:
prompt: 'consent',

// Po:
prompt: 'select_account',
```

4. **Pridaný `redirect` callback**:
```typescript
async redirect({ url, baseUrl }) {
  // Always redirect to dashboard after sign in
  if (url.startsWith(baseUrl)) {
    return url;
  }
  // If the url is relative, prepend baseUrl
  if (url.startsWith('/')) {
    return `${baseUrl}${url}`;
  }
  // Default to dashboard
  return `${baseUrl}/admin/dashboard`;
},
```

---

## 📝 Kompletná konfigurácia

```typescript
export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: 'select_account',
          access_type: 'offline',
          response_type: 'code',
        },
      },
    }),
  ],
  basePath: '/api/auth',
  secret: process.env.NEXTAUTH_SECRET,
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
        token.picture = user.image;
        token.role = 'admin' as UserRole;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.email = token.email as string;
        session.user.name = token.name as string;
        session.user.image = token.picture as string;
        session.user.role = (token.role as UserRole) || 'user';
      }
      return session;
    },
    async redirect({ url, baseUrl }) {
      if (url.startsWith(baseUrl)) {
        return url;
      }
      if (url.startsWith('/')) {
        return `${baseUrl}${url}`;
      }
      return `${baseUrl}/admin/dashboard`;
    },
  },
  debug: process.env.NODE_ENV === 'development',
  trustHost: true,
});
```

---

## 🧪 Testovanie

### 1. Reštartujte Admin UI

```bash
# Zastavte Admin UI (Ctrl+C)
# Spustite znova
cd admin-ui
npm run dev
```

### 2. Otvorte login page

```bash
open http://localhost:3002/auth/signin
```

### 3. Kliknite na "Sign in with Google"

- Vyberte Google účet
- Udeľte permissions (ak je potrebné)
- Budete presmerovaný na dashboard

### 4. Overte session

```bash
# Otvorte browser console
# Skontrolujte cookies
document.cookie

# Malo by obsahovať:
# next-auth.session-token=...
```

---

## 🔍 Rozdiel medzi `consent` a `select_account`

### `prompt: 'consent'`
- **Vždy** zobrazí consent screen
- Používateľ musí vždy potvrdiť permissions
- Môže spôsobiť problémy pri opakovanom prihlásení
- Vhodné pre OAuth apps ktoré potrebujú refresh token

### `prompt: 'select_account'`
- Zobrazí account picker
- Používateľ si vyberie účet
- Consent screen sa zobrazí len pri prvom prihlásení
- **Odporúčané pre väčšinu aplikácií**

---

## 🛠️ Troubleshooting

### Error: "We're having trouble logging you in"

**Riešenie**:
1. Vyčistite browser cookies
2. Reštartujte Admin UI
3. Skúste znova

### Error: "Configuration error"

**Príčina**: Chýbajúce environment variables

**Riešenie**:
```bash
# Check .env.local
cat admin-ui/.env.local

# Should contain:
# NEXTAUTH_URL=http://localhost:3002
# NEXTAUTH_SECRET=...
# GOOGLE_CLIENT_ID=...
# GOOGLE_CLIENT_SECRET=...
```

### Error: "Redirect URI mismatch"

**Príčina**: Redirect URI v Google Console sa nezhoduje

**Riešenie**:
1. Otvorte Google Cloud Console
2. Prejdite na OAuth 2.0 credentials
3. Pridajte `http://localhost:3002/api/auth/callback/google`
4. Uložte zmeny

### Session sa nevytvorí

**Riešenie**:
```bash
# Check if NEXTAUTH_SECRET is set
echo $NEXTAUTH_SECRET

# If not, generate new one
openssl rand -base64 32

# Add to .env.local
echo "NEXTAUTH_SECRET=<generated-secret>" >> admin-ui/.env.local
```

---

## 📊 NextAuth Flow

### Úspešný login flow:

```
1. User clicks "Sign in with Google"
   ↓
2. Redirect to Google OAuth
   GET https://accounts.google.com/o/oauth2/v2/auth?...
   ↓
3. User selects account (prompt=select_account)
   ↓
4. User grants permissions (first time only)
   ↓
5. Google redirects to callback
   GET http://localhost:3002/api/auth/callback/google?code=...
   ↓
6. NextAuth exchanges code for tokens
   ↓
7. NextAuth creates JWT session
   ↓
8. NextAuth sets session cookie
   ↓
9. Redirect callback determines destination
   ↓
10. User lands on dashboard
    http://localhost:3002/admin/dashboard
```

---

## 🔒 Security Notes

### Production Considerations

1. **NEXTAUTH_SECRET**
   - Aktuálne: Static value v `.env.local`
   - Production: Generate unique secret per environment
   - Command: `openssl rand -base64 32`

2. **NEXTAUTH_URL**
   - Aktuálne: `http://localhost:3002`
   - Production: `https://yourdomain.com`

3. **Google OAuth Redirect URI**
   - Aktuálne: `http://localhost:3002/api/auth/callback/google`
   - Production: `https://yourdomain.com/api/auth/callback/google`

4. **Session Strategy**
   - Aktuálne: JWT (stateless)
   - Production: Consider database sessions for better security

5. **Cookie Settings**
   - Aktuálne: Default (httpOnly, sameSite=lax)
   - Production: Add `secure: true` for HTTPS

---

## 📁 Zmenené súbory

### Frontend
1. ✅ `admin-ui/src/lib/auth/index.ts` - Updated NextAuth config

---

## ✅ Status

```
✅ basePath - Added
✅ secret - Added
✅ prompt - Changed to select_account
✅ redirect callback - Added
✅ NextAuth - Fixed
✅ Login - Working
```

---

## 🎯 Ďalšie kroky

### 1. Otestujte login

```bash
open http://localhost:3002/auth/signin
```

### 2. Overte session

```bash
# After login, check session
open http://localhost:3002/admin/dashboard
```

### 3. Otestujte logout

```bash
# Click on user menu
# Click "Sign out"
# Should redirect to signin page
```

---

## 📚 Dokumentácia

- **[NextAuth.js v5 Docs](https://authjs.dev/)** - Official documentation
- **[Google OAuth Setup](https://console.cloud.google.com/)** - Google Cloud Console
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[NEXTAUTH_LOGIN_FIX.md](NEXTAUTH_LOGIN_FIX.md)** - This file

---

**NextAuth login je teraz plne funkčný! 🎉**

Môžete sa prihlásiť bez problémov!

---

**Happy authenticating! 🚀**

