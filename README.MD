RUN FRONTEND --- python -m http.server 5500
RUN BACKEND --- uvicorn app.main:app --reload
RUN DATABASE ---
python app/database/db_session.py init
RUN SEED ---
python app/database/db_session.py seed
RUN

🔧 Creating admin authentication tables...
✅ Admin tables created successfully!
👑 Creating super admin account...
✅ Super admin created successfully!
Username: admin
Email: admin@coinvibe.com
Password: 2-weoueJxWdMkicnvDaoag
⚠️ IMPORTANT: Save this password securely - it won't be shown again!

#### curent one

Super admin created successfully!
Username: admin
Email: admin@coinvibe.com
Password: TPRvcvHC8Wxft8s_ZsVvMA
IMPORTANT: Save this password securely.
