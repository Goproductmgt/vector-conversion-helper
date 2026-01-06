# **Vector Conversion Helper — Frontend PRD**

**Version:** 1.0  
 **Date:** January 6, 2026  
 **Status:** Ready for Development  
 **Backend API:** Live and tested ✅

---

## **1\. Executive Summary**

### **What We're Building**

A simple, fast, free web interface that lets print shop workers convert raster images (JPG, PNG, HEIC) into print-ready vector files (SVG, EPS, PDF) in under 10 seconds.

### **Why It Matters**

Print shops waste hours manually tracing customer-submitted graphics. This tool eliminates that work by providing instant, automated vectorization with full color support.

### **Target User**

**Primary:** Print shop employees who receive low-resolution or raster graphics from customers and need scalable vector versions for printing.

**User Characteristics:**

* Not technical (no design software expertise)  
* Busy (processing multiple jobs daily)  
* Need speed over perfection  
* Value "good enough" output that works

### **Success Metric**

A print shop worker can go from "customer sent a JPG" to "I have print-ready vector files" in under 15 seconds total (including upload time).

---

## **2\. User Story & Job to Be Done**

### **Core User Story**

As a print shop team member,  
 I want to upload a raster image and receive print-ready vector files automatically,  
 so I can prepare jobs without manual tracing or workflow interruption.

### **Job to Be Done**

**When:** A customer brings in a low-resolution logo, flyer graphic, or icon  
 **I want to:** Convert it to a scalable vector format  
 **So I can:** Use it for business cards, banners, signs, or any print job at any size

### **User Context**

Print shops commonly handle:

* Business cards (logos \+ icons \+ decorative elements)  
* Flyers (event graphics, promotional icons)  
* Posters (large graphics that need to scale)  
* Banners (must scale to huge sizes without pixelation)  
* Menus (food icons, decorative elements)  
* Yard signs, door hangers, postcards, stickers

**Graphics that work well:**

* Company logos (simple, 1-3 colors)  
* Icons (social media, navigation, decorative)  
* Simple illustrations (clip art style)  
* Text-based graphics (badges, stamps, seals)  
* Geometric shapes (arrows, stars, borders)  
* Line drawings  
* Symbols and emblems

**Not designed for:**

* Complex photographs  
* Detailed artwork with smooth gradients  
* High-fidelity illustrations with many colors

---

## **3\. Product Requirements**

### **Functional Requirements**

| ID | Requirement | Priority |
| ----- | ----- | ----- |
| FR-1 | User can upload JPG, PNG, or HEIC files | Must Have |
| FR-2 | User sees upload progress indicator | Must Have |
| FR-3 | User sees processing status with stage info | Must Have |
| FR-4 | User can download SVG, EPS, and PDF outputs | Must Have |
| FR-5 | User sees clear error messages when conversion fails | Must Have |
| FR-6 | User can see before/after preview of their image | Should Have |
| FR-7 | User can start a new conversion without page refresh | Should Have |
| FR-8 | User can drag-and-drop files to upload | Should Have |
| FR-9 | User sees estimated processing time | Nice to Have |

### **Non-Functional Requirements**

| ID | Requirement | Target |
| ----- | ----- | ----- |
| NFR-1 | Page loads in under 2 seconds | Performance |
| NFR-2 | Works on mobile devices | Responsiveness |
| NFR-3 | Accessible to screen readers | Accessibility |
| NFR-4 | No user account required | Simplicity |
| NFR-5 | No configuration options shown | Simplicity |
| NFR-6 | Works in all modern browsers | Compatibility |

---

## **4\. User Flow**

### **Happy Path Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                        LANDING STATE                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │          🖼️  Drop your image here                        │  │
│  │              or click to browse                           │  │
│  │                                                           │  │
│  │          Supports: JPG, PNG, HEIC (max 10MB)             │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│         "Convert raster images to print-ready vectors"          │
│                    Free • Fast • Full Color                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (user uploads file)
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING STATE                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │    [████████████░░░░░░░░░░░░░░░░░░░░░░] 40%              │  │
│  │                                                           │  │
│  │    Stage: Removing background...                         │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│              Processing typically takes 5-10 seconds            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (processing complete)
┌─────────────────────────────────────────────────────────────────┐
│                       COMPLETE STATE                            │
│                                                                 │
│    ┌─────────────────┐      ┌─────────────────┐                │
│    │                 │      │                 │                │
│    │    ORIGINAL     │  →   │    VECTORIZED   │                │
│    │    (preview)    │      │    (preview)    │                │
│    │                 │      │                 │                │
│    └─────────────────┘      └─────────────────┘                │
│                                                                 │
│    ✅ Conversion complete!                                      │
│                                                                 │
│    Download your files:                                         │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│    │ ⬇️ SVG   │  │ ⬇️ EPS   │  │ ⬇️ PDF   │                    │
│    └──────────┘  └──────────┘  └──────────┘                    │
│                                                                 │
│              [ Convert Another Image ]                          │
└─────────────────────────────────────────────────────────────────┘
```

### **Error State Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│                        ERROR STATE                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │    ⚠️  Couldn't convert this image                       │  │
│  │                                                           │  │
│  │    This image is too complex for automatic conversion.   │  │
│  │    Works best with: logos, icons, simple graphics.       │  │
│  │                                                           │  │
│  │    [ Try a Different Image ]                             │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## **5\. API Specification**

### **Base URL**

```
https://8a0ad783-ee4c-45c7-b837-9def0ba1df34-00-38fayssaiyb0b.riker.replit.dev
```

*(Note: This is the current dev URL. Will be updated to permanent URL after Replit publishing.)*

### **Endpoints**

#### **POST /api/upload**

Upload an image file for conversion.

**Request:**

```
POST /api/upload
Content-Type: multipart/form-data

file: <binary image data>
```

**Success Response (200):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2026-01-06T14:30:00Z"
}
```

**Error Responses:**

| Status | Error Code | Message |
| ----- | ----- | ----- |
| 400 | INVALID\_FILE\_TYPE | File must be JPG, PNG, or HEIC |
| 400 | FILE\_TOO\_LARGE | File exceeds 10MB limit |
| 500 | PROCESSING\_FAILED | Failed to process image |

---

#### **GET /api/status/{job\_id}**

Check processing status.

**Response (200):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 65,
  "stage": "Vectorizing image...",
  "created_at": "2026-01-06T14:30:00Z",
  "updated_at": "2026-01-06T14:30:05Z"
}
```

**Status Values:**

| Status | Meaning |
| ----- | ----- |
| `queued` | Job received, waiting to start |
| `processing` | Currently being processed |
| `completed` | Done, files ready for download |
| `failed` | Error occurred |

**Progress Stages:**

| Progress | Stage |
| ----- | ----- |
| 0-10% | Validating image... |
| 10-40% | Removing background... |
| 40-80% | Vectorizing image... |
| 80-100% | Generating output formats... |

---

#### **GET /api/result/{job\_id}**

Get completed job results with download URLs.

**Success Response (200):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "files": {
    "original": "/api/files/550e8400.../original.png",
    "svg": "/api/files/550e8400.../output.svg",
    "eps": "/api/files/550e8400.../output.eps",
    "pdf": "/api/files/550e8400.../output.pdf"
  },
  "metadata": {
    "original_format": "png",
    "original_size_bytes": 245760,
    "processing_time_seconds": 8.4
  },
  "created_at": "2026-01-06T14:30:00Z",
  "completed_at": "2026-01-06T14:30:08Z"
}
```

**Failed Job Response:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error_code": "TOO_COMPLEX",
  "error_message": "Image has too many colors or gradients. Works best with simple logos and icons.",
  "retry_allowed": false
}
```

---

#### **GET /api/files/{job\_id}/{filename}**

Download a specific file.

**Response:** Binary file data with appropriate Content-Type header.

---

#### **GET /api/health**

Health check endpoint.

**Response (200):**

```json
{
  "status": "healthy",
  "service": "vector-conversion-helper"
}
```

---

## **6\. UI/UX Requirements**

### **Design Principles**

1. **Clarity Over Cleverness**

   * No jargon (don't say "rasterize" or "trace")  
   * Use plain language ("Convert to vector")  
   * Clear visual hierarchy  
2. **Speed Perception**

   * Show progress immediately after upload  
   * Use smooth progress bar animation  
   * Display current stage in human terms  
3. **Trust Building**

   * Show before/after preview  
   * Display processing time  
   * "Free" prominently displayed  
4. **Error Recovery**

   * Clear explanation of what went wrong  
   * Guidance on what images work best  
   * Easy path to try again

### **Visual Design Guidelines**

**Color Palette (suggested):**

* Primary action: Blue (\#3B82F6) or Green (\#10B981)  
* Success: Green (\#22C55E)  
* Error: Red (\#EF4444)  
* Background: Light gray (\#F9FAFB)  
* Text: Dark gray (\#1F2937)

**Typography:**

* Clean, readable sans-serif (Inter, SF Pro, or system fonts)  
* Large touch targets for mobile  
* High contrast text

**Layout:**

* Single-column, centered content  
* Generous whitespace  
* Mobile-first responsive design  
* Max content width \~600px

### **Accessibility Requirements**

* WCAG 2.1 AA compliance minimum  
* Keyboard navigation for all actions  
* Screen reader compatible  
* Focus indicators visible  
* Color not sole indicator of state  
* Alt text for all images

---

## **7\. Technical Specifications**

### **Recommended Frontend Stack**

**Option A: Simple & Fast (Recommended for MVP)**

* Next.js 14+ (App Router)  
* Tailwind CSS  
* TypeScript  
* Deployed on Vercel

**Option B: Lightweight Alternative**

* React \+ Vite  
* Tailwind CSS  
* TypeScript  
* Deployed anywhere

### **Key Implementation Notes**

1. **File Upload**

   * Use native `<input type="file">` with accept attribute  
   * Implement drag-and-drop with ondragover/ondrop  
   * Client-side validation before upload (file type, size)  
   * Show upload progress using XMLHttpRequest or fetch with ReadableStream  
2. **Polling for Status**

   * After upload, poll `/api/status/{job_id}` every 1-2 seconds  
   * Stop polling when status is `completed` or `failed`  
   * Implement exponential backoff if needed  
   * Max poll time: 60 seconds, then show timeout error  
3. **File Downloads**

   * Use anchor tags with `download` attribute  
   * Construct full URLs: `${API_BASE}${file_path}`  
   * Consider opening SVG preview in new tab  
4. **Error Handling**

   * Catch network errors separately from API errors  
   * Show user-friendly messages  
   * Log technical details to console for debugging  
5. **CORS**

   * Backend already configured with CORS `*` for MVP  
   * No special headers needed

### **Environment Variables**

```
NEXT_PUBLIC_API_URL=https://8a0ad783-ee4c-45c7-b837-9def0ba1df34-00-38fayssaiyb0b.riker.replit.dev
```

---

## **8\. Content & Copy**

### **Page Title**

"Vector Conversion Helper — Free Image to Vector Converter"

### **Tagline Options**

* "Convert raster images to print-ready vectors"  
* "From JPG to SVG in seconds"  
* "Make any image print-ready"

### **Upload Area Copy**

**Heading:** "Drop your image here"  
 **Subtext:** "or click to browse"  
 **Supported formats:** "Supports: JPG, PNG, HEIC (max 10MB)"

### **Processing States**

* "Validating image..."  
* "Removing background..."  
* "Vectorizing image..."  
* "Generating output formats..."  
* "Almost done..."

### **Success State**

**Heading:** "Conversion complete\!"  
 **Subtext:** "Download your files below"

### **Error Messages**

| Error Code | User-Friendly Message |
| ----- | ----- |
| INVALID\_FILE\_TYPE | "This file type isn't supported. Please use JPG, PNG, or HEIC." |
| FILE\_TOO\_LARGE | "This file is too large. Maximum size is 10MB." |
| TOO\_COMPLEX | "This image is too complex for automatic conversion. Works best with simple logos and icons." |
| PROCESSING\_FAILED | "Something went wrong. Please try again or use a different image." |
| NETWORK\_ERROR | "Couldn't connect to the server. Please check your internet and try again." |
| TIMEOUT | "Processing took too long. Please try a simpler image." |

### **Footer Copy**

"Free tool by \[Company Name\] • No account required • Files processed securely"

---

## **9\. Testing Requirements**

### **Manual Test Cases**

| Test Case | Steps | Expected Result |
| ----- | ----- | ----- |
| Happy path PNG | Upload valid PNG logo | Conversion completes, 3 files downloadable |
| Happy path JPG | Upload valid JPG image | Conversion completes, 3 files downloadable |
| Invalid file type | Upload a .txt file | Error: "This file type isn't supported" |
| File too large | Upload 15MB image | Error: "This file is too large" |
| Network error | Disconnect during upload | Error: "Couldn't connect to the server" |
| Mobile upload | Upload from mobile device | Same experience as desktop |
| Drag and drop | Drag file onto upload area | File uploads correctly |
| Download SVG | Click SVG download | File downloads with correct name |
| Download EPS | Click EPS download | File downloads with correct name |
| Download PDF | Click PDF download | File downloads with correct name |
| Convert another | Click "Convert Another" | Returns to upload state |

### **Browser Testing Matrix**

| Browser | Desktop | Mobile |
| ----- | ----- | ----- |
| Chrome | ✅ Required | ✅ Required |
| Safari | ✅ Required | ✅ Required |
| Firefox | ✅ Required | Should work |
| Edge | Should work | Should work |

---

## **10\. Out of Scope (Do NOT Build)**

To keep the MVP focused, explicitly exclude:

* ❌ User accounts or authentication  
* ❌ Batch processing (multiple files at once)  
* ❌ Image editing capabilities  
* ❌ Output quality settings  
* ❌ Color picker or palette extraction  
* ❌ History of past conversions  
* ❌ Sharing or collaboration features  
* ❌ Payment or premium tiers  
* ❌ Analytics dashboard  
* ❌ Admin interface

---

## **11\. Success Criteria**

### **Launch Criteria (MVP Complete When)**

* \[ \] User can upload JPG, PNG, or HEIC file  
* \[ \] User sees progress during processing  
* \[ \] User can download SVG, EPS, and PDF files  
* \[ \] User sees clear error messages  
* \[ \] Works on mobile Chrome and Safari  
* \[ \] Page loads in under 3 seconds  
* \[ \] Accessible via keyboard navigation

### **Post-Launch Metrics to Track**

1. **Conversion rate:** % of uploads that complete successfully  
2. **Time to download:** Seconds from upload to first download click  
3. **Error rate:** % of uploads that result in errors  
4. **Return usage:** % of users who convert multiple images

---

## **12\. Timeline & Milestones**

### **Suggested Development Phases**

**Phase 1: Core Upload & Display (Day 1-2)**

* File upload component  
* Basic API integration  
* Processing state display  
* Download links

**Phase 2: Polish & Error Handling (Day 3\)**

* Error state UI  
* Mobile responsiveness  
* Loading states  
* Drag-and-drop

**Phase 3: Testing & Launch (Day 4\)**

* Cross-browser testing  
* Mobile testing  
* Deploy to production  
* Connect to live API

---

## **13\. Reference Materials**

### **Backend Repository**

https://github.com/Goproductmgt/vector-conversion-helper

### **Live API (Current Dev URL)**

https://8a0ad783-ee4c-45c7-b837-9def0ba1df34-00-38fayssaiyb0b.riker.replit.dev

### **API Health Check**

```shell
curl https://8a0ad783-ee4c-45c7-b837-9def0ba1df34-00-38fayssaiyb0b.riker.replit.dev/api/health
```

### **Test Upload Command**

```shell
curl -X POST \
  -F "file=@test-image.png" \
  https://8a0ad783-ee4c-45c7-b837-9def0ba1df34-00-38fayssaiyb0b.riker.replit.dev/api/upload
```

---

## **14\. Appendix: Error Code Reference**

| Code | HTTP Status | Description |
| ----- | ----- | ----- |
| INVALID\_FILE\_TYPE | 400 | File is not JPG, PNG, or HEIC |
| FILE\_TOO\_LARGE | 400 | File exceeds 10MB limit |
| PROCESSING\_FAILED | 500 | General processing error |
| VECTORIZATION\_FAILED | 500 | VTracer couldn't process image |
| BACKGROUND\_REMOVAL\_FAILED | 500 | rembg couldn't remove background |
| TOO\_COMPLEX | 422 | Image unsuitable for vectorization |
| JOB\_NOT\_FOUND | 404 | Invalid job\_id |
| TIMEOUT | 408 | Processing exceeded 30 seconds |

---

**Document Version:** 1.0  
 **Last Updated:** January 6, 2026  
 **Author:** Backend Team  
 **Next Step:** Hand off to frontend team for implementation

