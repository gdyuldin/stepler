"""
Glance steps.

@author: schipiga@mirantis.com
"""

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from waiting import wait

from stepler.base import BaseSteps
from stepler.third_party.steps_checker import step

__all__ = [
    'GlanceSteps'
]


class GlanceSteps(BaseSteps):
    """Glance steps."""

    @step
    def create_image(self, image_name, image_path, disk_format='qcow2',
                     container_format='bare', check=True):
        """Step to create image

        Args:
            image_name (str): name of created image
            image_path (str): path to image at local machine
            disk_format (str): format of image disk
            container_format (str): format of image container
            check (bool): flag whether to check step or not

        Returns:
            object: glance image
        """
        image = self._client.images.create(name=image_name,
                                           disk_format=disk_format,
                                           container_format=container_format)
        self._client.images.upload(image.id, open(image_path, 'rb'))

        if check:
            self.check_image_status(image, 'active', timeout=180)

        return image

    @step
    def delete_image(self, image, check=True):
        """Step to delete image

        Args:
            image (object): glance image
            check (bool): flag whether to check step or not
        """
        self._client.images.delete(image.id)

        if check:
            self.check_image_presence(image, present=False, timeout=180)

    @step
    def create_images(self, image_names, image_path, disk_format='qcow2',
                      container_format='bare', check=True):
        """Step to create images

        Args:
            image_names (list): names of created images
            image_path (str): path to image at local machine
            disk_format (str): format of image disk
            container_format (str): format of image container
            check (bool): flag whether to check step or not

        Returns:
            list: glance images
        """
        images = []
        for image_name in image_names:
            image = self.create_image(image_name, image_path, disk_format,
                                      container_format, check=False)
            images.append(image)

        if check:
            for image in images:
                self.check_image_status(image, 'active', timeout=180)

        return images

    @step
    def delete_images(self, images, check=True):
        """Step to delete images

        Args:
            image (object): glance image
            check (bool): flag whether to check step or not
        """
        for image in images:
            self.delete_image(image, check=False)

        if check:
            for image in images:
                self.check_image_presence(image, present=False, timeout=180)

    @step
    def bind_project(self, image, project, check=True):
        """Step to bind image to project

        Args:
            image (object): image to bind to project
            project (object): project to bind to image
            check (bool): flag whether to check binding or not
        """
        self._client.image_members.create(image.id, project.id)
        self.check_image_bind_status(image, project)

    @step
    def unbind_project(self, image, project, check=True):
        """Step to unbind image to project

        Args:
            image (object): image to unbind from project
            project (object): project to unbind from image
            check (bool): flag whether to check unbinding or not
        """
        self._client.image_members.delete(image.id, project.id)
        self.check_image_bind_status(image, project, binded=False)

    @step
    def check_image_presence(self, image, present=True, timeout=0):
        """Check step image presence status

        Args:
            image (object): glance image to check presence status
            presented (bool): flag whether image should present or no
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutError: if check was falsed after timeout
        """
        def predicate():
            try:
                self._client.images.get(image.id)
                return present
            except Exception:
                return not present

        wait(predicate, timeout_seconds=timeout)

    @step
    def check_image_status(self, image, status, timeout=0):
        """Check step image status

        Args:
            image (object): glance image to check status
            status (str): image status name to check
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutError: if check was falsed after timeout
        """
        def predicate():
            image.update(self._client.images.get(image.id))
            return image.status.lower() == status.lower()

        wait(predicate, timeout_seconds=timeout)

    @step
    def check_image_bind_status(self, image, project, binded=True, timeout=0):
        """Check step image binding status

        Args:
            image (object): image binded/unbinded with project
            project (object): project binded/unbinded with image
            binded (bool): flag whether project and image should be binded or
                           unbinded
            timeout (int): seconds to wait a result of check

        Raises:
            TimeoutError: if check was falsed after timeout
        """
        def predicate():
            members = self._client.image_members.list(image.id)
            member_ids = [member['member_id'] for member in members]

            if binded:
                return project.id in member_ids
            else:
                return project.id not in member_ids

        wait(predicate, timeout_seconds=timeout)
