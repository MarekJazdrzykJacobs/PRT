from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content, Email as _Email_, To
from .Text import Text

class Email:
    """
    The class allows sending email messages.
    """

    __slots__ = ['sg']

    def __init__(self, api_key: str = None):

        if api_key:
            # Make a connectin to SendGrid
            self.sg = SendGridAPIClient(api_key = api_key)


    def send_message(self, from_email: str, to_email: str, email_subject: str, email_content: str, name: str):

        """
        The method allows to send email via sendgrid API.

        :parameter
            from_email (str): who is sending email
            to_email (str): recipient
            email_subject (str): title of email
            email_content (str): content of email
            name (str): who send message

        :return
            API response. 202 if accomplished
        """

        #Define the message details
        from_email = _Email_(from_email, name)
        to_email = To(to_email)
        email_content = Content("text/plain", email_content)

        #Build sendgrid email object
        email= Mail(from_email, to_email, email_subject, email_content)

        #Convert email to json
        email_json = email.get()

        #Send email
        response = self.sg.client.mail.send.post(request_body = email_json)

        return response.status_code


    @staticmethod
    def convert_email_address(email_address: str):
        """
        The method is used to converting email address to below pattern:
        first.second@jacobs.com --> First.Second@jacobs.com

        :parameter
            email_address (str): email address to be converted

        :return
            email_address (str): converted email address
        """

        #Remove tabs and spaces from start/end of email address
        email_address = Text.remove_spaces(text = email_address, on_start = True, on_end = True)

        #Take names and domain
        names, domain = email_address.split('@')

        #Convert string to list
        names = [i.lower() for i in names]

        #Convert first character in email address to upper case
        names[0] = names[0].upper()

        #Go thru each character and make as uppercase first character after '.'
        for idx, i in enumerate(names):
            if i == '.' and idx + 1 != len(names):
                names[idx + 1] = names[idx + 1].upper()

        #Convert list to string
        names = ''.join(names)

        return f'{names}@{domain}'