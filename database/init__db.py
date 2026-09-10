from migrate import migrate

if __name__ == "__main__":
    applied = migrate()
    if applied:
        print(f"Database initialized. Applied migrations: {applied}")
    else:
        print("Database already up to date.")
