# form_filler.py
from faker import Faker
from playwright.sync_api import Page, Locator

fake = Faker()

class FormFiller:
    def __init__(self):
        # Maps input names/types to faker functions for plausible data
        self.filler_map = {
            'email': fake.email,
            'name': fake.name,
            'first_name': fake.first_name,
            'last_name': fake.last_name,
            'company': fake.company,
            'phone': fake.phone_number,
            'address': fake.address,
            'city': fake.city,
            'state': fake.state,
            'zip': fake.zipcode,
            'country': fake.country,
            'text': fake.sentence,
            'password': fake.password,
        }

    def fill_form(self, page_or_locator: Page | Locator):
        """
        Finds all visible input fields in a given scope (page or form locator) and fills them.
        """
        print("  -> Attempting to fill form...")
        # Text, email, password, etc. inputs
        for input_element in page_or_locator.locator('input[type="text"], input[type="email"], input[type="password"], input[type="tel"], textarea').all():
            if not input_element.is_visible():
                continue
            
            name = input_element.get_attribute("name") or ""
            input_type = input_element.get_attribute("type") or "text"
            
            # Find the best fake data to use
            key_to_try = next((key for key in self.filler_map if key in name.lower()), input_type)
            data_generator = self.filler_map.get(key_to_try, fake.word)
            
            try:
                input_element.fill(data_generator())
            except Exception as e:
                print(f"    - Could not fill input '{name}': {e}")

        # Checkboxes and Radio buttons
        for checkbox in page_or_locator.locator('input[type="checkbox"], input[type="radio"]').all():
            if checkbox.is_visible():
                try:
                    checkbox.check()
                except Exception as e:
                    print(f"    - Could not check box: {e}")
                    
        # Select dropdowns
        for select in page_or_locator.locator('select').all():
             if select.is_visible():
                try:
                    # Select the second option (skipping any "Please select" default)
                    options = select.locator('option').all()
                    if len(options) > 1:
                        select.select_option(index=1)
                except Exception as e:
                     print(f"    - Could not select option: {e}")