

def check_for_get_code(code, url):
        """
        Check that we got the expected code when accessing url via GET.
        Returns the response.
        """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, code,
                         "got code %d for url '%s'. Expected code %d"
                         % (resp.status_code, url, code))
        return resp


def check_for_post_code(code, url, data={}):
        """
        Check that we got the expected code when accessing url via POST.
        Returns the response.
        """
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, code,
                         "got code %d for url '%s'. Expected code %d"
                         % (resp.status_code, url, code))
        return resp
