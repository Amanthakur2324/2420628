# Notification System Design

## Stage 1 – REST API + Real‑time

**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications?studentId=123&limit=20` | Fetch paginated |
| PUT | `/api/notifications/{id}/read` | Mark as read |
| PUT | `/api/notifications/read-all` | Mark all read |
| DELETE | `/api/notifications/{id}` | Delete |

**Headers**: `Authorization: Bearer <token>`, `Content-Type: application/json`

**Real‑time**: WebSockets (Socket.IO) – each student joins room = `studentId`. Server emits `new_notification` on creation.

## Stage 2 – Database Schema (PostgreSQL)

```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id INT NOT NULL REFERENCES students(id),
    type VARCHAR(20) CHECK (type IN ('Placement','Event','Result')),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notif_student_read_created 
    ON notifications(student_id, is_read, created_at DESC);


' # Stage 3 '    

SELECT DISTINCT s.id, s.name
FROM students s
JOIN notifications n ON s.id = n.student_id
WHERE n.type = 'Placement' AND n.created_at >= NOW() - INTERVAL '7 days';

'# Stage 4'