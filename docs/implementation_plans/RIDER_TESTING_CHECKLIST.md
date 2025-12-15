# 🧪 RIDER SYSTEM - TESTING CHECKLIST

## ✅ PRE-TESTING SETUP

1. **Create Test Rider Account**
   ```
   - Go to /users/register/
   - Select "Rider" role
   - Fill in details
   - Login
   ```

2. **Admin Setup**
   ```
   - Go to /admin/
   - Find the rider in Users
   - Set verification_status to 'VERIFIED'
   - Save
   ```

---

## 📋 TESTING CHECKLIST

### **1. Rider Settings Page** (`/users/rider/settings/`)

- [ ] Page loads without errors
- [ ] Active status toggle works (online/offline)
- [ ] Profile photo upload works
- [ ] Personal info form saves correctly
- [ ] Vehicle change request form works
- [ ] Reason field is required
- [ ] Pending request shows up
- [ ] Can't submit duplicate requests
- [ ] Location settings save correctly
- [ ] Delete account link works

### **2. Admin Panel** (`/admin/`)

- [ ] VehicleChangeRequest appears in admin
- [ ] Can view all requests
- [ ] Can filter by status
- [ ] Can search by rider name
- [ ] Approve action works
- [ ] Reject action works
- [ ] Rider profile updates after approval
- [ ] Admin notes save correctly

### **3. Rider Dashboard** (`/users/dashboard/`)

- [ ] Dashboard loads without errors
- [ ] Stats cards display correctly
- [ ] Active jobs section shows assigned orders
- [ ] New requests section shows available orders
- [ ] QR code button works
- [ ] QR modal opens
- [ ] QR code generates
- [ ] Order details display in modal
- [ ] Phone links work (clickable)
- [ ] Accept job button works
- [ ] Mark as picked up works
- [ ] Mark as delivered works
- [ ] Performance stats update

### **4. Public Profile** (`/users/rider/profile/<username>/`)

- [ ] Profile loads for other users
- [ ] Shows verification badge
- [ ] Shows availability status
- [ ] Displays stats correctly
- [ ] Reviews section works
- [ ] Settings button (only for owner)
- [ ] QR code modal works

### **5. QR Code System**

- [ ] QR code generates on button click
- [ ] Contains correct order data
- [ ] Displays farmer information
- [ ] Displays buyer information
- [ ] Shows locations
- [ ] Phone numbers are clickable
- [ ] Modal closes properly
- [ ] Works on mobile devices

### **6. Workflow Testing**

**Complete Delivery Flow:**
1. [ ] Create order as farmer
2. [ ] Rider sees in "New Requests"
3. [ ] Rider taps "Scan QR"
4. [ ] QR modal shows all details
5. [ ] Rider taps "Accept Job"
6. [ ] Job moves to "Active Jobs"
7. [ ] Rider taps "Mark as Picked Up"
8. [ ] Status updates
9. [ ] Rider taps "Mark as Delivered"
10. [ ] Order completes
11. [ ] Stats update automatically

**Vehicle Change Flow:**
1. [ ] Rider goes to Settings
2. [ ] Fills vehicle change form
3. [ ] Provides reason
4. [ ] Submits request
5. [ ] Pending badge shows
6. [ ] Admin sees request
7. [ ] Admin approves
8. [ ] Rider profile updates
9. [ ] Rider sees new vehicle info

---

## 🐛 COMMON ISSUES TO CHECK

### **Template Errors**
- [ ] No template syntax errors
- [ ] All variables render correctly
- [ ] No missing context variables
- [ ] Bootstrap classes work

### **JavaScript Errors**
- [ ] QR code library loads
- [ ] No console errors
- [ ] Modal opens/closes
- [ ] AJAX calls work

### **Database Errors**
- [ ] Migrations applied
- [ ] No foreign key errors
- [ ] Data saves correctly
- [ ] Queries are optimized

### **Security**
- [ ] Login required for all pages
- [ ] Role verification works
- [ ] CSRF tokens present
- [ ] Can't access other riders' settings

### **Mobile Responsiveness**
- [ ] Works on iPhone (375px)
- [ ] Works on iPad (768px)
- [ ] Works on desktop (1920px)
- [ ] Buttons are tappable
- [ ] Text is readable

---

## 🔍 DETAILED TEST CASES

### **Test Case 1: New Rider Registration**
```
1. Go to /users/register/?role=RIDER
2. Fill form with valid data
3. Submit
4. Should redirect to dashboard
5. Should see "Pending Verification" alert
6. Should NOT see any delivery requests
```

### **Test Case 2: Verified Rider Workflow**
```
1. Admin verifies rider
2. Rider refreshes dashboard
3. Should see "Verified" badge
4. Should see available delivery requests
5. Can accept requests
6. Can update delivery status
```

### **Test Case 3: Vehicle Change Request**
```
1. Go to Settings
2. Fill vehicle change form:
   - New Type: Pickup
   - New Plate: KBZ 456C
   - Reason: "Bought new vehicle"
3. Submit
4. Should see success message
5. Should see pending request card
6. Try to submit another → Should fail
7. Admin approves
8. Refresh settings
9. Should see new vehicle info
10. Pending request should disappear
```

### **Test Case 4: QR Code Functionality**
```
1. Have an available order
2. Click "Scan QR" button
3. Modal should open
4. QR code should generate
5. Should see:
   - Order number
   - Farmer name, phone, location
   - Buyer name, phone, location
6. Click farmer phone → Should open dialer
7. Click buyer phone → Should open dialer
8. Close modal
9. QR should clear
10. Open again → New QR generates
```

### **Test Case 5: Performance Tracking**
```
1. Note current stats
2. Accept a delivery
3. Mark as picked up
4. Mark as delivered
5. Check stats:
   - Completed deliveries +1
   - Active jobs -1
   - Success rate updated
6. Refresh page
7. Stats should persist
```

---

## 📊 EXPECTED RESULTS

### **Dashboard Stats**
- Completed Deliveries: Increases with each completion
- Active Jobs: Shows current assigned orders
- Success Rate: Percentage (completed / total)
- Rating: Average of all reviews

### **QR Code Data**
```json
{
  "order_id": "123",
  "farmer": {
    "name": "John Farmer",
    "phone": "0712345678",
    "location": "Nairobi, Westlands"
  },
  "buyer": {
    "name": "Jane Buyer",
    "phone": "0723456789",
    "location": "Nairobi, Parklands"
  },
  "timestamp": "2025-12-13T18:00:00Z"
}
```

### **Vehicle Change Request**
- Status: PENDING → APPROVED
- Rider profile updates automatically
- Old values preserved in request
- Admin notes visible

---

## 🚨 CRITICAL TESTS

**MUST PASS:**
1. [ ] Verified riders can accept jobs
2. [ ] Unverified riders CANNOT accept jobs
3. [ ] QR codes generate correctly
4. [ ] Phone links work
5. [ ] Stats update after delivery
6. [ ] Vehicle changes require approval
7. [ ] Can't submit duplicate change requests
8. [ ] Settings only accessible by owner
9. [ ] All forms have CSRF protection
10. [ ] Mobile responsive on all pages

---

## ✅ SIGN-OFF

**Tested By:** _______________
**Date:** _______________
**Environment:** Development / Staging / Production
**Status:** Pass / Fail
**Notes:** _______________

---

## 🐛 BUG REPORTING TEMPLATE

```
**Bug Title:** 
**Page:** 
**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Result:** 
**Actual Result:** 
**Screenshots:** 
**Browser:** 
**Device:** 
**Priority:** High / Medium / Low
```

---

**TESTING STATUS: READY FOR QA ✅**
