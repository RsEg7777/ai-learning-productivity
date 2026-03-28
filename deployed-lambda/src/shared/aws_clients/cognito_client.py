"""Amazon Cognito client for user authentication."""

import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CognitoClient:
    """Client for Amazon Cognito operations."""

    def __init__(
        self,
        user_pool_id: str,
        client_id: str,
        region: Optional[str] = None,
    ) -> None:
        """
        Initialize Cognito client.

        Args:
            user_pool_id: Cognito User Pool ID
            client_id: Cognito App Client ID
            region: AWS region (optional)
        """
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region or "us-east-1"
        self.client = boto3.client("cognito-idp", region_name=self.region)
        logger.info(f"Initialized CognitoClient for user pool: {user_pool_id}")

    def sign_up(
        self,
        username: str,
        password: str,
        email: str,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            username: Username
            password: Password
            email: Email address
            attributes: Additional user attributes

        Returns:
            Sign up response

        Raises:
            ClientError: If sign up fails
        """
        try:
            user_attributes = [
                {"Name": "email", "Value": email},
            ]

            if attributes:
                for key, value in attributes.items():
                    user_attributes.append({"Name": key, "Value": value})

            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=username,
                Password=password,
                UserAttributes=user_attributes,
            )

            logger.info(f"Successfully signed up user: {username}")
            return response

        except ClientError as e:
            logger.error(f"Failed to sign up user: {e}")
            raise

    def confirm_sign_up(self, username: str, confirmation_code: str) -> None:
        """
        Confirm user sign up with verification code.

        Args:
            username: Username
            confirmation_code: Verification code

        Raises:
            ClientError: If confirmation fails
        """
        try:
            self.client.confirm_sign_up(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
            )
            logger.info(f"Successfully confirmed sign up for user: {username}")
        except ClientError as e:
            logger.error(f"Failed to confirm sign up: {e}")
            raise

    def initiate_auth(
        self,
        username: str,
        password: str,
    ) -> Dict[str, Any]:
        """
        Initiate authentication.

        Args:
            username: Username
            password: Password

        Returns:
            Authentication response with tokens

        Raises:
            ClientError: If authentication fails
        """
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password,
                },
            )

            logger.info(f"Successfully authenticated user: {username}")
            return response

        except ClientError as e:
            logger.error(f"Failed to authenticate user: {e}")
            raise

    def respond_to_auth_challenge(
        self,
        session: str,
        challenge_name: str,
        challenge_responses: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Respond to authentication challenge (e.g., MFA).

        Args:
            session: Session from initial auth
            challenge_name: Challenge name
            challenge_responses: Challenge responses

        Returns:
            Authentication response

        Raises:
            ClientError: If response fails
        """
        try:
            response = self.client.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName=challenge_name,
                Session=session,
                ChallengeResponses=challenge_responses,
            )

            logger.info(f"Successfully responded to auth challenge: {challenge_name}")
            return response

        except ClientError as e:
            logger.error(f"Failed to respond to auth challenge: {e}")
            raise

    def get_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from access token.

        Args:
            access_token: Access token

        Returns:
            User information

        Raises:
            ClientError: If retrieval fails
        """
        try:
            response = self.client.get_user(AccessToken=access_token)
            logger.info("Successfully retrieved user information")
            return response
        except ClientError as e:
            logger.error(f"Failed to get user: {e}")
            raise

    def update_user_attributes(
        self,
        access_token: str,
        attributes: Dict[str, str],
    ) -> None:
        """
        Update user attributes.

        Args:
            access_token: Access token
            attributes: Attributes to update

        Raises:
            ClientError: If update fails
        """
        try:
            user_attributes = [{"Name": key, "Value": value} for key, value in attributes.items()]

            self.client.update_user_attributes(
                AccessToken=access_token,
                UserAttributes=user_attributes,
            )

            logger.info("Successfully updated user attributes")
        except ClientError as e:
            logger.error(f"Failed to update user attributes: {e}")
            raise

    def change_password(
        self,
        access_token: str,
        previous_password: str,
        proposed_password: str,
    ) -> None:
        """
        Change user password.

        Args:
            access_token: Access token
            previous_password: Current password
            proposed_password: New password

        Raises:
            ClientError: If password change fails
        """
        try:
            self.client.change_password(
                AccessToken=access_token,
                PreviousPassword=previous_password,
                ProposedPassword=proposed_password,
            )
            logger.info("Successfully changed password")
        except ClientError as e:
            logger.error(f"Failed to change password: {e}")
            raise

    def forgot_password(self, username: str) -> None:
        """
        Initiate forgot password flow.

        Args:
            username: Username

        Raises:
            ClientError: If request fails
        """
        try:
            self.client.forgot_password(
                ClientId=self.client_id,
                Username=username,
            )
            logger.info(f"Initiated forgot password for user: {username}")
        except ClientError as e:
            logger.error(f"Failed to initiate forgot password: {e}")
            raise

    def confirm_forgot_password(
        self,
        username: str,
        confirmation_code: str,
        new_password: str,
    ) -> None:
        """
        Confirm forgot password with code.

        Args:
            username: Username
            confirmation_code: Verification code
            new_password: New password

        Raises:
            ClientError: If confirmation fails
        """
        try:
            self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=new_password,
            )
            logger.info(f"Successfully reset password for user: {username}")
        except ClientError as e:
            logger.error(f"Failed to confirm forgot password: {e}")
            raise

    def sign_out(self, access_token: str) -> None:
        """
        Sign out user globally.

        Args:
            access_token: Access token

        Raises:
            ClientError: If sign out fails
        """
        try:
            self.client.global_sign_out(AccessToken=access_token)
            logger.info("Successfully signed out user")
        except ClientError as e:
            logger.error(f"Failed to sign out user: {e}")
            raise

    def delete_user(self, access_token: str) -> None:
        """
        Delete user account.

        Args:
            access_token: Access token

        Raises:
            ClientError: If deletion fails
        """
        try:
            self.client.delete_user(AccessToken=access_token)
            logger.info("Successfully deleted user account")
        except ClientError as e:
            logger.error(f"Failed to delete user: {e}")
            raise
