import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.services.dify_service import dify_client

async def main():
    db = SessionLocal()
    users = db.query(User).filter(User.dify_private_dataset_id == None).all()
    for user in users:
        print(f"Creating dataset for user: {user.username}")
        try:
            dataset_id = await dify_client.create_empty_dataset(user.username)
            if dataset_id:
                user.dify_private_dataset_id = dataset_id
                db.commit()
                print(f"Successfully created and assigned dataset {dataset_id} to user {user.username}")
        except Exception as e:
            print(f"Failed for user {user.username}: {e}")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
