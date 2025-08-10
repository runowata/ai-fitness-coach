# Pull Request Template

## 📝 Description
Brief description of changes and motivation behind them.

## 🎯 Type of Change
- [ ] 🚀 New feature
- [ ] 🐛 Bug fix  
- [ ] 🔧 Refactoring
- [ ] 📚 Documentation
- [ ] 🧪 Tests
- [ ] ⚡ Performance improvement
- [ ] 💥 Breaking change

## 🧪 Testing
- [ ] Tests added/updated and passing
- [ ] Manual testing completed
- [ ] No regressions identified

### Test Commands
```bash
# Quick smoke test
python manage.py check
python manage.py makemigrations --check

# Unit tests
pytest -q -m "unit" --maxfail=1

# Integration tests  
pytest -q -m "integration" --maxfail=1

# Full test suite with coverage
pytest -q --cov=apps --cov-report=term-missing
```

## 🔍 Code Quality
- [ ] Code follows project style (black, isort, flake8)
- [ ] No hardcoded values or secrets
- [ ] Error handling implemented
- [ ] Logging added where appropriate
- [ ] Documentation updated

### Quality Commands
```bash
# Code formatting
black . --line-length 100
isort . --profile=black
flake8 --max-line-length=100
```

## 🚢 Deployment
- [ ] Migrations safe for production
- [ ] Environment variables documented
- [ ] Backwards compatible
- [ ] Database queries optimized

### Migration Safety
```bash
# Check migrations on clean DB
python manage.py migrate
python manage.py migrate --plan
```

## 📋 Checklist
- [ ] Self-review completed
- [ ] PR title follows convention
- [ ] Related issues linked
- [ ] Breaking changes documented
- [ ] Performance impact assessed

## 🔗 Related Issues
Fixes #(issue_number)
Related to #(issue_number)

## 📸 Screenshots/Logs
_Add screenshots for UI changes or logs for debugging_

## ⚠️ Breaking Changes
_List any breaking changes and migration steps_

## 📚 Additional Notes
_Any additional context, deployment notes, or follow-up items_

---

### For Reviewers
- **Focus areas:** _Specific areas needing attention_
- **Testing strategy:** _How to test these changes_
- **Deployment considerations:** _Any special deployment needs_