from django.contrib.auth.tokens import PasswordResetTokenGenerator

class VendorTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, vendor, timestamp):
        # Ensure that the hash is invalidated when the password changes
        return (
            str(vendor.pk) + str(timestamp) +
            str(vendor.password_hash)
        )

vendor_token_generator = VendorTokenGenerator()
