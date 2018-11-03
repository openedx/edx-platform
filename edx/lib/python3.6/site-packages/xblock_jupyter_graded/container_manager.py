import logging
import os
from subprocess import Popen, PIPE
import pkg_resources

from config import EDX_ROOT
from models import Requirement
from exceptions import DockerBuildError

log = logging.getLogger(__name__)


class ContainerManager(object):
    def __init__(self, course_id):
        self.course_id = course_id

    def set_requirements(self, packages):
        """Clears packages for course and sets new values"""
        # Clean newlines from packages
        packages = [pkg for pkg in (i.strip() for i in packages) if pkg]

        Requirement.objects.filter(course=self.course_id).delete()
        log.info("Cleared packages for course: {}".format(self.course_id))
        for pkg in packages:
            values = pkg.split("==")
            name = values[0]
            version = values[1] if len(values) > 1 else None
            req = Requirement.objects.create(
                course=self.course_id,
                package_name=name,
                version=version
            )
            log.info("Added req: {} to course: {}".format(req, self.course_id))

    def update_requirements(self, packages):
        """Update Requirement table with new packages
        
        Uses newest version of conflicting packages. If no version specified,
        indicates to use to most recent version so stores it without a version

        Not currently used.
        """

        # Clean newlines from packages
        packages = [pkg for pkg in (i.strip() for i in packages) if pkg]
        log.info("Updates requirements.txt for course: {}".format(self.course_id))
        log.debug("New Packages: {}".format(packages))

        # Create package dicts
        current_pkg_dict = self._build_pkg_dict(self.get_package_list())
        new_pkg_dict = self._build_pkg_dict(packages)

        # Update new packages
        for new_pkg, new_v in new_pkg_dict.items():
            # Add pkg if not currently in requirements
            if new_pkg not in current_pkg_dict:
                current_pkg_dict[new_pkg] = new_v

            # Update version if it's a newer package
            else:
                log.info("existing pkg found: {}".format(new_pkg))
                if new_v is None:
                    current_pkg_dict[new_pkg] = None
                elif current_pkg_dict[new_pkg] is None:
                    pass
                elif new_v > current_pkg_dict[new_pkg]:
                    current_pkg_dict[new_pkg] = new_v

        # Write out new requirements
        updated_packages = []
        for name, vers in current_pkg_dict.items():
            string = "{}=={}".format(name, vers) if vers else name
            updated_packages.append(string)
        self.set_requirements(updated_packages)

    def _build_pkg_dict(self, pkg_string_list):
        """Return dict of pkg_name: version from list of pkg==version strings"""
        pkg_list = [i.split("==") for i in pkg_string_list]
        pkg_dict = {}
        for i in pkg_list:
            pkg_dict[i[0]] = i[1] if len(i) > 1 else None
        return pkg_dict

    def get_package_list(self):
        """Return list of currently installed packages in pkg==ver format
        
        Returned format is same as a common requirements.txt file:
            pkg==ver (pinned version)
            pkg (non-pinned verion - install most recent)

        does not support other requirements.txt formats and may throw an 
        exception or have undefined behavior (eg, git+, etc)
        """
        packages = Requirement.objects.filter(course=self.course_id)\
            .order_by('package_name')
        pkg_list = packages.values_list('package_name', 'version')
        pkg_strings = []
        for pkg in pkg_list:
            string = "{}=={}".format(pkg[0], pkg[1]) if pkg[1] else pkg[0]
            pkg_strings.append(string)
        return pkg_strings

    def build_container(self):
        """Builds docker container for course using model Requirements"""
        packages = self.get_package_list()
        packages = self._add_ipykernel(packages)
        pkg_str = " ".join(packages)
        log.info("Building container for course: {}".format(self.course_id))
        log.info("Building with packages: {}".format(packages))

        # Get path to Dockerfile directory
        dockerfile_path = pkg_resources.resource_filename(__name__, 'docker/')

        # Build Docker Container
        # NOTE: installing pacakges via a list instead of pip install -r b/c 
        # otherwise we'd have to copy requirements.txt into dockerfile folder
        # for each build. Could get a race condtion if multiple people are
        # building at the same time

        cmd = [
            'sudo', '-u', 'jupyter', 'docker', 'build', dockerfile_path,
            '-t', self.course_id.lower(),
            '--build-arg', 'PACKAGES={}'.format(pkg_str)
        ]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        
        # Evaluate output
        if p.returncode != 0:
            log.info("OUT")
            log.info(out)
            log.info("ERR")
            log.info(err)
            raise DockerBuildError(out.decode('utf-8'))

    def _add_ipykernel(self, package_strs):
        """Adds ipykernel to package list if it is not present"""
        found = False
        for pkg_str in package_strs:
            if 'ipykernel' in pkg_str:
                found = True
                log.info("Skip adding ipykernel to package list; already found")
                return package_strs

        if not found:
            log.info("Added ipykernel to package list")
            package_strs.append('ipykernel')

        return package_strs


    def container_exists(self):
        """Returns True if a container image exists"""
        cmd = [
            'sudo', '-u', 'jupyter',
            'docker', 'inspect', '--type=image', self.course_id
        ]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        return p.returncode == 0 

    def cleanup(self):
        """Runs `docker system prune -f` to remove dangling images"""
        log.info("Cleaning up dangling docker images via docker system prune")
        cmd = [
            'sudo', '-u', 'jupyter', 'docker', 'system', 'prune', '-f',
        ]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        # Evaluate output
        if p.returncode != 0:
            log.debug("OUT")
            log.debug(out)
            log.debug("ERR")
            log.debug(err)
            raise DockerBuildError(out.decode('utf-8'))
        log.info(out.decode('utf-8'))


        




