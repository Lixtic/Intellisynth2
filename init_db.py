from app.database import Base, engine
from app.models.log import LogEntry

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
