#!/usr/bin/env python3
"""
Push Sambo Bot files to GitHub using a personal access token
Version 2 - With better error handling and output
"""

import os
import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"\n📝 {description}...")
    print(f"   Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success!")
        if result.stdout:
            print(f"   Output: {result.stdout[:200]}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed!")
        print(f"   Error: {e.stderr[:500]}")
        return False
    except Exception as e:
        print(f"❌ {description} - Exception!")
        print(f"   Error: {str(e)[:500]}")
        return False

def main():
    try:
        print("\n" + "=" * 70)
        print("🥋 Sambo Bot - GitHub Push Script (Version 2)")
        print("=" * 70)
        
        # Get inputs from user
        print("\n📋 Please provide the following information:\n")
        
        github_token = input("Enter your GitHub token (ghp_...): ").strip()
        if not github_token:
            print("❌ GitHub token is required!")
            input("Press Enter to exit...")
            sys.exit(1)
        
        github_username = input("Enter your GitHub username (e.g., johnaaiton-art): ").strip()
        if not github_username:
            print("❌ GitHub username is required!")
            input("Press Enter to exit...")
            sys.exit(1)
        
        repo_name = input("Enter repository name (e.g., sambo-habit-developer): ").strip()
        if not repo_name:
            print("❌ Repository name is required!")
            input("Press Enter to exit...")
            sys.exit(1)
        
        project_path = input("Enter the FULL path to sambo-habit-developer folder: ").strip()
        # Remove quotes if user added them
        project_path = project_path.strip('"').strip("'")
        
        if not os.path.exists(project_path):
            print(f"❌ Path does not exist: {project_path}")
            print(f"   Current directory: {os.getcwd()}")
            print(f"   Files here: {os.listdir('.')[:5]}")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Check if it's a valid project folder
        if not os.path.exists(os.path.join(project_path, 'bot.py')):
            print(f"⚠️  Warning: bot.py not found in {project_path}")
            print(f"   Files in folder: {os.listdir(project_path)[:10]}")
        
        # Change to project directory
        os.chdir(project_path)
        print(f"\n📂 Working in: {os.getcwd()}")
        print(f"   Files: {', '.join(os.listdir('.')[:5])}...")
        
        # Initialize git if not already initialized
        if not os.path.exists(os.path.join(project_path, '.git')):
            print("\n🔧 Initializing git repository...")
            run_command("git init", "Initialize git repository")
        else:
            print("\n✅ Git repository already initialized")
        
        # Configure git
        print("\n🔐 Configuring git credentials...")
        run_command(f'git config user.name "{github_username}"', "Set git username")
        run_command(f'git config user.email "{github_username}@github.com"', "Set git email")
        
        # Check git status
        print("\n📊 Checking git status...")
        run_command("git status", "Git status")
        
        # Add all files
        print("\n📦 Adding files...")
        if not run_command("git add .", "Add all files"):
            print("⚠️  Warning: Could not add files, but continuing...")
        
        # Check what will be committed
        run_command("git status", "Files to commit")
        
        # Commit
        print("\n💾 Committing files...")
        if not run_command('git commit -m "Add complete Sambo Habits Tracking Bot with all documentation and deployment files"', "Commit files"):
            print("⚠️  Warning: Commit may have failed or no changes to commit")
        
        # Rename branch to main if needed
        print("\n🌿 Setting up main branch...")
        run_command("git branch -M main", "Rename branch to main")
        
        # Remove existing remote if it exists
        print("\n🔗 Configuring remote...")
        run_command("git remote remove origin", "Remove existing remote (if any)")
        
        # Add remote with token authentication
        remote_url = f"https://{github_username}:{github_token}@github.com/{github_username}/{repo_name}.git"
        # Don't print the full URL with token for security
        print(f"   Remote URL: https://github.com/{github_username}/{repo_name}.git")
        if not run_command(f'git remote add origin "{remote_url}"', "Add remote repository"):
            print("❌ Failed to add remote")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Verify remote
        run_command("git remote -v", "Verify remote")
        
        # Push to GitHub
        print("\n🚀 Pushing to GitHub...")
        print("   This may take a moment...")
        if run_command("git push -u origin main", "Push to GitHub"):
            print("\n" + "=" * 70)
            print("✅ SUCCESS! Your bot is now on GitHub!")
            print("=" * 70)
            print(f"\n📍 Repository: https://github.com/{github_username}/{repo_name}")
            print("\n📚 Next steps:")
            print("1. Go to https://railway.app")
            print("2. Create a new project and connect your GitHub repository")
            print("3. Set the environment variables in Railway dashboard:")
            print("   - TELEGRAM_BOT_TOKEN")
            print("   - GOOGLE_SHEET_ID")
            print("   - GOOGLE_CREDENTIALS_JSON")
            print("   - DEEPSEEK_API_KEY")
            print("\n4. Railway will automatically deploy your bot!")
            print("\n📖 For detailed setup, see README.md in your repository")
            print("\n" + "=" * 70)
        else:
            print("\n❌ Failed to push to GitHub")
            print("Possible reasons:")
            print("  1. Token doesn't have 'repo' scope permissions")
            print("  2. Repository doesn't exist yet")
            print("  3. Network connectivity issue")
            print("\nTry these fixes:")
            print("  1. Create the repository manually on GitHub first")
            print("  2. Check your token permissions at https://github.com/settings/tokens")
            print("  3. Try running the script again")
        
        input("\nPress Enter to exit...")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
