"""
Init database to create table schema and dummy data
"""
from database import get_db_session, engine
from model import Base, TV_CHANNEL


def init_db():
    Base.metadata.create_all(bind=engine)


def init_channel(db_session):
    try:
        tv_channel = ["MBC", "SBS", "JTBC", "TVN", "KBS",
                      "MNET", "CHANNEL S", "YOUTUBE", "TV ING"]
        db_session.add_all([TV_CHANNEL(name=channel)
                            for channel in tv_channel])
    except Exception:
        raise


def main():
    init_db()
    with get_db_session() as db_session:
        init_channel(db_session)
        db_session.commit()


if __name__ == "__main__":
    main()
