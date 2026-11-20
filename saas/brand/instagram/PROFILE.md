# @replyinbox.in Instagram profile kit

Upload from this folder. All images are 1080×1080 and safe for Instagram's circle crop.

| Field | Value |
|---|---|
| Profile photo | `profile-photo.png` |
| Name (searchable, 26/64 chars; Instagram rejects names containing "Instagram") | `ReplyInbox | DM Automation` |
| Category | Software |
| Website / link | `https://replyinbox.in` |
| Email (contact button) | `support@replyinbox.in` |

## Bio (143/150 characters)

```
Auto-reply to every comment & DM, 24/7 💬
AI replies in Hindi, Hinglish & English 🇮🇳
Free plan · Official Meta login 🔒
👇 Start free in 2 minutes
```

## Highlights (cover → what to put in it)

| Cover | Title | Stories to add |
|---|---|---|
| `highlight-start.png` | Start | How to sign up and connect Instagram (3–4 screen recordings) |
| `highlight-demo.png` | Demo | A comment → DM happening live; the AI reply in Hinglish |
| `highlight-features.png` | Features | Auto DM, follow-to-unlock, AI Inbox, link in bio, content plan |
| `highlight-pricing.png` | Pricing | Free / Starter / Creator / Pro / Agency, one plan per story |
| `highlight-reviews.png` | Reviews | Creator screenshots and results (add once you have them) |
| `highlight-help.png` | Help | FAQs, "DM HELP", support@replyinbox.in |

## First posts (pin 3)

Pin three carousels from `saas/content/carousels/`: `comment-to-dm` (what it does), `ai-dm-agent` (the AI),
and a comparison such as `manychat` (why ReplyInbox). Each folder has the caption and the automation for its
keyword; make the slides with `python3 tools/carousels.py comment-to-dm ai-dm-agent manychat` (from `saas/`).

Regenerate the images: `node brand/instagram/ig_kit.js brand/instagram` (from `saas/`): dark violet glow, the brand
mark, thin violet → coral gradient rings with line icons.
