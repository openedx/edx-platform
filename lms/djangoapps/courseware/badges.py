"""
Defines BadgeCollection, a class which stores data about badges as various objects, and which fetches this data from
settings.BADGE_SERVICE_URL when instantiated.
"""

import json
import requests

from django.conf import settings


class BadgeCollection(object):
    """
    Stores instances of Badge.
    Provides helper methods to make retrieving badge data easier from the template.
    """
    def get_badges(self):
        """
        Return all badges.
        """
        return self.badges

    def get_earned_badges(self):
        """
        Return only earned badges.
        """
        earned_badges = [badge for badge in self.badges if badge.is_earned]
        return earned_badges

    def get_unlockable_badges(self):
        """
        Return only unearned ("unlockable") badges.
        """
        unlockable_badges = [badge for badge in self.badges if not badge.is_earned]
        return unlockable_badges

    def get_badge_urls(self):
        """
        Return a list of URLs pointing to where json for each badge may be accessed.
        This is returned as a json-dumped string so that it may be inserted in a Javascript call from a template.
        """
        earned_badges = self.get_earned_badges()
        badge_urls = [badge.href for badge in earned_badges]
        return json.dumps(badge_urls)

    def __init__(self, email, course_id=None):
        """
        Create a BadgeCollection by fetching data from the badging service about the badges belonging to `email`.

        If `course_id` is specified, only those badges specific to that course will be returned, including both
        earned badges and unearned badges.

        If `course_id` is not specified, then all of the earned badges belonging to `email` will be returned, without
        information about unearned badges.
        """
        if course_id is not None:

            # Filter badges by the student's email and by the course ID.
            badges_url = '/v1/badges/.json?badgeclass__issuer__course={course}&email={email}'
            raw_badges = _fetch(badges_url.format(course=course_id, email=email))

            # Get the list of all badgeclasses for this course.
            raw_badgeclasses = _fetch('/v1/badgeclasses/.json?issuer__course={course}'.format(course=course_id))

        else:
            # No course: only filter badges by the student's email, and display no unearned badges.
            badges_url = '/v1/badges/.json?email={email}'
            raw_badges = _fetch(badges_url.format(email=email))

            raw_badgeclasses = [
                _fetch(badge['badge'])
                for badge in raw_badges
            ]

        # Reformat raw_badges into this dictionary -- badgeclass_url: badge_data
        # Note that badgeclass_url is stored under the keyword 'badge'
        badges_dict = dict(
            (badge['badge'], badge)
            for badge in raw_badges
        )

        # Create self.badges.
        self.badges = []
        issuers_dict = {}

        for badgeclass_info in raw_badgeclasses:

            badgeclass = Badgeclass(badgeclass_info)

            # Keep track of which issuers have already been fetched, so that they don't need to be fetched twice.
            issuer_url = badgeclass.issuer
            if issuer_url not in issuers_dict.keys():
                issuer_info = _fetch(issuer_url)
                issuers_dict.update({issuer_url: issuer_info})

            issuer_info = issuers_dict[issuer_url]
            issuer = Issuer(issuer_info)

            # Instantiate the badge according to whether it has been earned or not.
            if badgeclass.href in badges_dict.keys():
                badge_info = badges_dict[badgeclass.href]
                badge = EarnedBadge(badge_info, badgeclass, issuer)
            else:
                badge = Badge(badgeclass, issuer)

            self.badges.append(badge)


class Badge(object):
    """
    Stores data about an unearned badge.
    """
    def __init__(self, badgeclass, issuer):
        """
        Create a badge, storing its badgeclass and issuer.

        `badgeclass` an instance of Badgeclass
        `issuer` an instance of Issuer

        Raises TypeError if objects of incorrect type are passed in.
        Raises BadgingServiceError if improperly formatted data is passed in.
        """
        if type(badgeclass) is not Badgeclass:
            raise TypeError('Passed in a non-Badgeclass to Badge.__init__')
        if type(issuer) is not Issuer:
            raise TypeError('Passed in a non-Issuer to Badge.__init__')

        self.badgeclass = badgeclass
        self.issuer = issuer
        self.is_earned = False


class EarnedBadge(Badge):
    """
    Stores data about an earned badge (a superset of the data stored about an unearned badge). Subclass of Badge.
    """
    def __init__(self, badge_info, badgeclass, issuer):
        """
        Use a subset of the data in badge_info to instantiate this badge.

        `badge_info` the JSON object about this badge that the badging service returned, already parsed from JSON
        `badgeclass` an instance of Badgeclass
        `issuer` an instance of Issuer

        Raises TypeError if objects of incorrect type are passed in.
        Raises BadgingServiceError if improperly formatted data is passed in.
        """
        super(EarnedBadge, self).__init__(badgeclass, issuer)

        try:
            self.href = badge_info['edx_href']
            self.image = badge_info['image']
            self.issued_on = badge_info['issuedOn']
        except KeyError:
            raise BadgingServiceError('Improperly formatted badge information')

        self.is_earned = True


class Badgeclass(object):
    """
    Stores data about a badgeclass -- all of the generic information defining a badge.
    """
    def __init__(self, badgeclass_info):
        """
        Use a subset of the data in badgeclass_info to instantiate this badgeclass.

        `badgeclass_info` the JSON object about this badgeclass that the badging service returned, already parsed from JSON

        Raises BadgingServiceError if improperly formatted data is passed in.
        """
        try:
            self.href = badgeclass_info['edx_href']
            self.issuer = badgeclass_info['issuer']
            self.name = badgeclass_info['name']
            self.description = badgeclass_info['description']
            self.criteria = badgeclass_info['criteria']
            self.image = badgeclass_info['image']
            self.number_awarded = badgeclass_info['edx_number_awarded']
        except KeyError:
            raise BadgingServiceError('Improperly formatted badgeclass information')


class Issuer(object):
    """
    Stores data about the issuer of a badge.
    """
    def __init__(self, issuer_info):
        """
        Use a subset of the data in issuer_info to instantiate this issuer.

        `issuer_info` the JSON object about this issuer that the badging service returned, already parsed from JSON

        Raises BadgingServiceError if improperly formatted data is passed in.
        """
        try:
            self.href = issuer_info['edx_href']
            self.name = issuer_info['name']
            self.url = issuer_info['url']
            self.course = issuer_info['edx_course']
        except KeyError:
            raise BadgingServiceError('Improperly formatted issuer information')


def _fetch(url):
    """
    Helper method. Reads the JSON object located at a URL. Returns the Python representation of the JSON object.

    If the fetched JSON object is a paginated list -- with the next url at 'next' and the content at 'results' --
    this reads through all of the pages, and compiles the results together into one list.

    Throws a BadgingServiceError if unsuccessful.
    """

    # Create absolute URL from relative URL.
    if not settings.BADGE_SERVICE_URL in url:
        url = settings.BADGE_SERVICE_URL + url

    try:
        obj = requests.get(url, timeout=10).json  # (.json is OK for our version of requests) # pylint: disable=E1103
    except requests.exceptions.RequestException:
        raise BadgingServiceError('URL not found: {url}'.format(url=url))

    results = obj.get('results', None)

    # Ensure that next results are obtained, if the output was paginated.
    if results is not None:
        next_url = obj.get('next', None)

        while next_url is not None:
            try:
                next_obj = requests.get(next_url, timeout=10).json  # pylint: disable=E1103
            except requests.exceptions.RequestException:
                raise BadgingServiceError('URL not found: {url}'.format(url=url))
            results.extend(next_obj.get('results', []))
            next_url = next_obj.get('next', None)

        return results

    else:
        return obj


class BadgingServiceError(Exception):
    """
    Custom class for passing around errors representing improper behavior by the badging service.
    """
    pass
