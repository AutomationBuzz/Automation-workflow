# Automation-workflow

Project mirror of [child-and-hope-social-agent](https://github.com/AutomationBuzz/child-and-hope-social-agent).

This repository is being initialized from the source project. To preserve the complete Git commit history, clone the source and push all branches and tags as documented below.

```bash
git clone https://github.com/AutomationBuzz/child-and-hope-social-agent.git
cd child-and-hope-social-agent
git remote rename origin upstream
git remote add origin https://github.com/AutomationBuzz/Automation-workflow.git
git push -u origin main
git push origin --all
git push origin --tags
```

GitHub Actions secrets, environments, and Jenkins credentials must be configured separately in the destination repository. Never commit secret tokens or `.env` files.