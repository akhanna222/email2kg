"""
Authentication API routes for user registration, login, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.db.models import User
from app.core.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_active_user
)
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    UserUpdate,
    PasswordChange,
    PreferencesUpdate
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_data: User registration data (email, password, full_name)
        db: Database session

    Returns:
        Created user data

    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,  # Can be used for email verification later
        gmail_connected=False,
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT access token.

    Args:
        user_credentials: User email and password
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user's information.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        User data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.

    Args:
        user_update: Updated user data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If email already exists
    """
    # Check if email is being changed and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = user_update.email

    # Update full name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user's password.

    Args:
        password_data: Current and new password
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If current password is incorrect
    """
    from app.core.auth import verify_password

    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.patch("/me/preferences", response_model=UserResponse)
async def update_user_preferences(
    preferences: PreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences.

    Args:
        preferences: Updated preferences
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data
    """
    # Initialize preferences if None
    if current_user.preferences is None:
        current_user.preferences = {}

    # Update email_sync_limit preference
    if preferences.email_sync_limit is not None:
        # 0 means unlimited, convert to None
        limit_value = None if preferences.email_sync_limit == 0 else preferences.email_sync_limit
        current_user.preferences['email_sync_limit'] = limit_value

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout user (client should discard token).

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # JWT tokens are stateless, so logout is handled client-side by discarding the token
    # This endpoint is mainly for client confirmation
    return {"message": "Logged out successfully"}
