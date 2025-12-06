# GitHub Setup Instructions

## If you already have a GitHub repository named "FiberTrace"

### 1. Add the remote and push

```bash
cd /Users/aminebaha/Desktop/FiberTrace
git remote add origin https://github.com/YOUR_USERNAME/FiberTrace.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## If you need to create a new repository

1. Go to https://github.com/new
2. Repository name: `FiberTrace`
3. Make it public or private (your choice)
4. **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"
6. Then run the commands above

## Cloning on Raspberry Pi

Once your code is pushed to GitHub, on your Raspberry Pi run:

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/FiberTrace.git
cd FiberTrace
```

Then follow the installation instructions in README.md.

