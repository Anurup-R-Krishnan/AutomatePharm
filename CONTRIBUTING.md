# Contributing to AutomatePharm

Thank you for your interest in contributing to the **AutomatePharm** project — **Selvam Medicals Pharmacy Management System**! This guide will help you understand how to contribute effectively.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

---

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- Virtual environment tool (venv)
- SQLite or PostgreSQL

### Setting Up Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/Anurup-R-Krishnan/AutomatePharm.git
cd AutomatePharm

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r SELVAM_MEDICALS\ fc/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your local settings

# 5. Start the backend
cd SELVAM_MEDICALS\ fc/backend
uvicorn main:app --reload --port 8000

# 6. Open frontend (in another terminal)
# Navigate to SELVAM_MEDICALS fc/frontend and open index.html in your browser
```

---

## Git Workflow

### Branch Naming Convention

We follow a structured branch naming pattern for clarity:

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<feature-name>` | `feat/add-payment-gateway` |
| Bug Fix | `fix/<bug-name>` | `fix/invoice-calculation-error` |
| Documentation | `docs/<doc-name>` | `docs/update-setup-guide` |
| Refactor | `refactor/<module>` | `refactor/inventory-module` |
| Test | `test/<feature-name>` | `test/billing-edge-cases` |
| DevOps | `chore/<task>` | `chore/upgrade-dependencies` |

### Example Workflow

```bash
# 1. Create a feature branch from main
git checkout main
git pull origin main
git checkout -b feat/add-loyalty-points

# 2. Make your changes
# ... edit files ...

# 3. Commit with conventional messages (see below)
git add .
git commit -m "feat: add loyalty points calculation module"

# 4. Push your branch
git push origin feat/add-loyalty-points

# 5. Open a Pull Request (PR)
# Go to GitHub and create a PR with a descriptive title and description
```

---

## Commit Message Format

We use **Conventional Commits** for clear, semantic commit history:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, semicolons, etc.)
- **refactor**: Code refactoring without functionality changes
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Build process, dependencies, tooling
- **ci**: CI/CD changes

### Scope (Optional but Recommended)

Scope refers to the feature or module affected:
- `billing`
- `inventory`
- `crm`
- `supplier`
- `reports`
- `security`
- `ai-models`

### Examples

```bash
# Simple feature
git commit -m "feat(billing): add GST calculation"

# Bug fix with scope
git commit -m "fix(inventory): resolve stock count discrepancy"

# Detailed commit with body and footer
git commit -m "feat(crm): implement customer loyalty points

- Add loyalty points accrual on purchases
- Add points redemption logic
- Update customer dashboard to show points balance

Closes #123"
```

---

## Code Standards

### Project Structure

Follow the existing modular architecture:

```
backend/
├── modules/
│   ├── <feature>/
│   │   ├── __init__.py
│   │   ├── router.py       FastAPI route handlers
│   │   ├── schemas.py      Pydantic request/response models
│   │   ├── service.py      Business logic
│   │   └── dependencies.py FastAPI dependencies
│   ├── security/
│   └── ...
├── models/
│   └── <model>.py          SQLAlchemy models
├── config.py               Configuration
├── database.py             Database setup
└── main.py                 FastAPI app entry point
```

### Naming Conventions

Follow these naming standards consistently:

| Element | Convention | Example |
|---------|-----------|---------|
| Functions | `snake_case` | `calculate_total_amount()` |
| Classes | `PascalCase` | `BillingService` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_INVOICE_ITEMS` |
| Variables | `snake_case` | `customer_id` |
| Private methods | `_snake_case` | `_validate_invoice()` |
| API routes | `/api/<module>/<resource>` | `/api/billing/invoice` |

### Code Style

- **Language**: Python 3.8+
- **Formatter**: `black`
- **Linter**: `ruff` or `flake8`
- **Type hints**: Use for public functions and classes
- **Docstrings**: Use Google-style docstrings

#### Example Function

```python
def calculate_invoice_total(items: list, gst_rate: float = 0.18) -> dict:
    """Calculate total invoice amount including GST.
    
    Args:
        items: List of billing items with prices.
        gst_rate: GST percentage (default: 18%).
        
    Returns:
        Dictionary with subtotal, tax, and grand_total.
        
    Raises:
        ValueError: If items list is empty or gst_rate is invalid.
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    if not 0 <= gst_rate <= 1:
        raise ValueError("GST rate must be between 0 and 1")
    
    subtotal = sum(item.price * item.quantity for item in items)
    tax = subtotal * gst_rate
    total = subtotal + tax
    
    return {
        "subtotal": subtotal,
        "tax": tax,
        "grand_total": total
    }
```

---

## Testing

### Writing Tests

All new features must include tests. We use `pytest` for testing.

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_billing.py

# Run with coverage
pytest --cov=backend tests/
```

#### Example Test

```python
# tests/test_billing.py
import pytest
from backend.modules.billing.service import calculate_invoice_total

def test_calculate_invoice_total():
    """Test invoice total calculation with GST."""
    items = [
        {"medicine_id": 1, "quantity": 2, "price": 100},
        {"medicine_id": 2, "quantity": 1, "price": 200},
    ]
    
    result = calculate_invoice_total(items, gst_rate=0.18)
    
    assert result["subtotal"] == 400
    assert result["tax"] == pytest.approx(72)
    assert result["grand_total"] == pytest.approx(472)
```

---

## Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows the naming conventions and style guidelines
- [ ] All functions have docstrings
- [ ] Tests are added/updated for new features
- [ ] No hardcoded secrets (use `.env`)
- [ ] Database migrations (if applicable) are documented
- [ ] Commit messages follow conventional format
- [ ] Branch is up-to-date with `main`
- [ ] No merge conflicts

---

## Documentation

### Update Relevant Documentation

- **README.md**: For user-facing changes
- **Module README**: For module-specific features
- **Code comments**: For complex logic
- **Docstrings**: For all public functions and classes

---

## Reporting Bugs

### Bug Report Template

```markdown
### Title
[Brief description of the bug]

### Steps to Reproduce
1. Step 1
2. Step 2
3. ...

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Environment
- Python version: 
- OS: 
- Branch/commit: 

### Logs/Screenshots
[Attach relevant logs or screenshots]
```

---

## Pull Request Guidelines

### PR Title Format

```
<type>(<scope>): <short-description>

Example: feat(billing): add multi-currency support
```

### PR Description Template

```markdown
## Description
Brief description of the changes.

## Related Issues
Closes #123

## Type of Change
- [ ] Feature
- [ ] Bug Fix
- [ ] Documentation
- [ ] Refactor

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing done

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed my own code
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## Local Validation Before Push

```bash
# 1. Format code
black SELVAM_MEDICALS\ fc/backend/

# 2. Lint code
ruff check SELVAM_MEDICALS\ fc/backend/

# 3. Run tests
pytest

# 4. Check for secrets
grep -r "password\|api_key\|secret" --include="*.py"

# 5. Verify no uncommitted changes interfere
git status
```

---

## Questions or Need Help?

- **Documentation**: Check README.md and module-specific guides
- **Issues**: Open a GitHub issue with detailed description
- **Discussions**: Use GitHub discussions for broader topics

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to AutomatePharm!
