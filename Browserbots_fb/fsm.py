class BrowserState:
    """
    FSM to track page load, popups, login, cart status.
    """
    def __init__(self):
        self.page_loaded = False
        self.popup_visible = False
        self.logged_in = False
        self.cart_updated = False

    def update(self, page):
        """Updates the state based on the current page content/visibility."""
        self.page_loaded = True
        try:
            self.popup_visible = page.is_visible('#popup-modal') 
        except:
            self.popup_visible = False
        try:
            self.logged_in = page.is_visible('#logout-button')
        except:
            self.logged_in = False
        try:
            self.cart_updated = page.is_visible('#cart-count')
        except:
            self.cart_updated = False
