import subprocess
import time
import sys

def run_command(command, title):
    full_cmd = f'start "{title}" cmd /k "{command}"'
    subprocess.Popen(full_cmd, shell=True)

def main():
    print("=== PRIVACY VISION LAUNCHER ===")
    
    # 1. Docker Check
    print("🐳 Checking Docker...")
    subprocess.run("docker-compose up -d", shell=True)
    time.sleep(5)

    # 2. Database Clear Option
    if input("\n🗑️  Clear Database? (y/n): ").lower() == 'y':
        subprocess.run('docker exec -i priv_eye_db psql -U admin -d smart_city_db -c "TRUNCATE TABLE footfall_logs;"', shell=True)
        print("✅ Database cleared.")

    print("\n🚀 Launching Windows...")
    run_command("python ai_consumer.py", "1. AI CONSUMER")
    time.sleep(1)
    run_command("streamlit run dashboard.py", "2. DASHBOARD")
    time.sleep(1)
    run_command("python camera_producer.py", "3. CAMERA PRODUCER")

    print("\n✅ System Live.")

if __name__ == "__main__":
    main()