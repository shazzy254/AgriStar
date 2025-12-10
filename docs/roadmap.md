# AgriStar Roadmap & Acceptance Criteria

## Acceptance Criteria

| Feature | Criteria |
|---------|----------|
| **User Auth** | - User can register as Farmer, Buyer, or Supplier.<br>- User can login and logout.<br>- Profile page shows correct role-specific fields.<br>- Password reset email is sent (console in dev). |
| **Community** | - User can post text and images.<br>- User can like and comment on posts.<br>- AI detects pests in images (mock).<br>- Feed shows latest posts. |
| **Marketplace** | - Seller can list products with images.<br>- Buyer can search/filter products.<br>- Buyer can place orders.<br>- Seller sees orders for their products. |
| **AI Assistant** | - Chatbot responds to queries (mock).<br>- Image diagnosis returns label/confidence.<br>- Translation endpoint works. |
| **Core** | - Farmer can add events to calendar.<br>- Notifications are received via WebSockets (mock/log). |

## Priority Roadmap (Sprint Plan)

### Sprint 1: Foundation & Auth (Week 1)
- [x] Project Scaffold & Docker Setup
- [x] User Models & Auth Views
- [x] Basic Templates (Register/Login)
- [ ] Deploy to Staging (Heroku/Render)

### Sprint 2: Community & Marketplace Core (Week 2)
- [x] Community Models & Feed
- [x] Marketplace Models & Product List
- [ ] Image Upload to S3 (Prod setup)
- [ ] Search Implementation (Refine)

### Sprint 3: AI & Advanced Features (Week 3)
- [x] AI Service Integration (Mock)
- [x] Calendar Feature
- [ ] Realtime Notifications (Frontend Integration)
- [ ] Multilingual UI (i18n setup)

### Sprint 4: Polish & Launch (Week 4)
- [ ] Unit & Integration Testing
- [ ] UI/UX Polish (Animations, Responsive checks)
- [ ] User Acceptance Testing
- [ ] Production Deployment
