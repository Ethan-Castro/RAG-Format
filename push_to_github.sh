#!/bin/bash

# Push to GitHub script for RAG Format application

echo "Setting up git configuration..."
git config --global user.name "Ethan-Castro"
git config --global user.email "your-email@example.com"  # Replace with your actual email

echo "Adding all files to git..."
git add -A

echo "Creating commit..."
git commit -m "Initial commit: RAG Format web scraper application with PDF/CSV generation and image scraping"

echo "Adding GitHub remote..."
# Using PAT in URL for authentication
git remote add origin https://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@github.com/Ethan-Castro/RAG-Format.git

echo "Pushing to GitHub..."
git push -u origin main

# If the branch is master instead of main, uncomment the next line and comment the above
# git push -u origin master

echo "Push complete! Your code is now on GitHub."