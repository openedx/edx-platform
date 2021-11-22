/* eslint-disable no-new */
import { ReactRenderer } from 'ReactRenderer';
import { StudentAccountDeletion } from './components/StudentAccountDeletion';

const maxWait = 60000;
const interval = 50;
const accountDeletionWrapperId = 'account-deletion-container';
let currentWait = 0;

const wrapperRendered = setInterval(() => {
  const wrapper = document.getElementById(accountDeletionWrapperId);

  if (wrapper) {
    clearInterval(wrapperRendered);
    new ReactRenderer({
      component: StudentAccountDeletion,
      selector: `#${accountDeletionWrapperId}`,
      componentName: 'StudentAccountDeletion',
      props: {
        socialAccountLinks: window.auth,
        isActive: window.isActive,
        additionalSiteSpecificDeletionText: window.additionalSiteSpecificDeletionText,
        mktgRootLink: window.mktgRootLink,
        platformName: window.platformName,
        siteName: window.siteName,
        mktgEmailOptIn: window.mktgEmailOptIn
      },
    });
  }

  currentWait += interval;

  if (currentWait >= maxWait) {
    clearInterval(wrapperRendered);
  }
}, interval);
