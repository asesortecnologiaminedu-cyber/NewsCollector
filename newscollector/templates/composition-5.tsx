// 'use client';

import { RiExternalLinkLine, RiInstanceLine } from '@remixicon/react';
import {
  Divider,
  Select,
  SelectItem,
  Tab,
  TabGroup,
  TabList,
  TextInput,
} from '@tremor/react';

// This example requires @tailwind/forms

// // tailwind.config.js
// module.exports = {
//   // ...
//   plugins: [
//     // ...
//     require('@tailwindcss/forms'),
//   ],
// }

export default function Example() {
  return (
    <>
      <h3 className="text-tremor-title font-bold text-tremor-content-strong dark:text-dark-tremor-content-strong">
        General
      </h3>
      <p className="mt-2 text-tremor-default leading-6 text-tremor-content dark:text-dark-tremor-content">
        Manage your personal details, workspace governance and notifications.
      </p>
      <TabGroup defaultIndex={1} className="mt-6">
        <TabList>
          <Tab>Account details</Tab>
          <Tab>Settings</Tab>
          <Tab>Billing</Tab>
        </TabList>
        {/* Content below only for demo purpose placed outside of <Tab> component. Add <TabPanels>, <TabPanel> to make it functional and to add content for other tabs */}
        <form action="#" method="POST">
          <div className="mt-8 rounded-tremor-small bg-tremor-background-muted p-6 ring-1 ring-inset ring-tremor-ring dark:bg-dark-tremor-background-muted dark:ring-dark-tremor-ring sm:max-w-7xl">
            <h4 className="text-tremor-default font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
              This workspace is currently on free plan
            </h4>
            <p className="mt-2 text-tremor-default text-tremor-content dark:text-dark-tremor-content">
              Boost your analytics and unlock advanced features with our premium
              plans.
            </p>
            <div className="mt-6 flex items-center space-x-2">
              <a
                href="#"
                className="inline-flex h-8 items-center whitespace-nowrap rounded-tremor-small bg-tremor-brand px-3 text-tremor-default font-medium text-tremor-brand-inverted shadow-tremor-input hover:bg-tremor-brand-emphasis dark:bg-dark-tremor-brand dark:text-dark-tremor-brand-inverted dark:shadow-dark-tremor-input dark:hover:bg-dark-tremor-brand-emphasis"
              >
                Compare Plans
              </a>
              <button
                type="button"
                className="inline-flex h-8 items-center whitespace-nowrap rounded-tremor-small border border-tremor-border bg-tremor-background px-3 py-2 text-tremor-default font-medium text-tremor-content shadow-tremor-input hover:text-tremor-content-emphasis dark:border-dark-tremor-border dark:bg-dark-tremor-background dark:text-dark-tremor-content dark:shadow-dark-tremor-input hover:dark:text-dark-tremor-content-emphasis"
              >
                Dismiss
              </button>
            </div>
          </div>
          <div className="mt-6 space-y-8 sm:max-w-lg">
            <div>
              <label className="text-tremor-default font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
                Name
              </label>
              <TextInput
                className="mt-2 rounded-tremor-small"
                disabled
                placeholder="sales-dashboard"
              />
              <p className="mt-2 text-tremor-label text-tremor-content dark:text-dark-tremor-content">
                Contact your admin to change workspace names in production.
              </p>
            </div>
            <div>
              <label
                htmlFor="select-input-1"
                className="text-tremor-default font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong"
              >
                Default model
              </label>
              <Select
                name="select-input-1"
                id="select-input-1"
                defaultValue="1"
                enableClear={false}
                className="mt-2 [&>*]:rounded-tremor-small"
              >
                <SelectItem value="1" icon={RiInstanceLine}>
                  GPT-3.5 (OpenAI)
                </SelectItem>
                <SelectItem value="2" icon={RiInstanceLine}>
                  BERT (Google)
                </SelectItem>
                <SelectItem value="3" icon={RiInstanceLine}>
                  LLaMA (Facebook)
                </SelectItem>
              </Select>
            </div>
            <div>
              <label
                htmlFor="select-input-2"
                className="text-tremor-default font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong"
              >
                Training cycle
              </label>
              <Select
                name="select-input-2"
                id="select-input-2"
                defaultValue="2"
                enableClear={false}
                className="mt-2 [&>*]:rounded-tremor-small"
              >
                <SelectItem value="1">Every 24 hours</SelectItem>
                <SelectItem value="2">Once in a week</SelectItem>
                <SelectItem value="3">Once in a month</SelectItem>
              </Select>
            </div>
            <div>
              <h4 className="text-tremor-default font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
                Workspace governance
              </h4>
              <div className="mt-6 space-y-6">
                <div className="relative flex items-start">
                  <div className="flex h-6 items-center">
                    <input
                      id="checkbox-name-1"
                      aria-describedby="checkbox-name-1-description"
                      name="checkbox-name-1"
                      type="checkbox"
                      className="size-4 rounded border-tremor-border text-tremor-brand shadow-tremor-input focus:ring-tremor-brand-muted dark:border-dark-tremor-border dark:bg-dark-tremor-background dark:text-dark-tremor-brand dark:shadow-dark-tremor-input dark:focus:ring-dark-tremor-brand-muted"
                    />
                  </div>
                  <div className="ml-3 text-tremor-default leading-6">
                    <label
                      htmlFor="checkbox-name-1"
                      className="font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong"
                    >
                      Require team member approval for deploy requests
                    </label>
                    <p
                      id="checkbox-name-1-description"
                      className="text-tremor-content dark:text-dark-tremor-content"
                    >
                      Lorem ipsum dolor sit amet, consetetur sadipscing elitr.
                    </p>
                  </div>
                </div>
                <div className="relative flex items-start">
                  <div className="flex h-6 items-center">
                    <input
                      id="checkbox-name-2"
                      aria-describedby="checkbox-name-2-description"
                      name="checkbox-name-2"
                      type="checkbox"
                      className="size-4 rounded border-tremor-border text-tremor-brand shadow-tremor-input focus:ring-tremor-brand-muted dark:border-dark-tremor-border dark:bg-dark-tremor-background dark:text-dark-tremor-brand dark:shadow-dark-tremor-input dark:focus:ring-dark-tremor-brand-muted"
                    />
                  </div>
                  <div className="ml-3 text-tremor-default leading-6">
                    <label
                      htmlFor="checkbox-name-2"
                      className="font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong"
                    >
                      Enable audit logs
                    </label>
                    <p
                      id="checkbox-name-2-description"
                      className="text-tremor-content dark:text-dark-tremor-content"
                    >
                      Lorem ipsum dolor sit amet.
                    </p>
                  </div>
                </div>
                <div className="relative flex items-start">
                  <div className="flex h-6 items-center">
                    <input
                      id="checkbox-name-3"
                      aria-describedby="checkbox-name-3-description"
                      name="checkbox-name-3"
                      type="checkbox"
                      className="size-4 rounded border-tremor-border text-tremor-brand shadow-tremor-input focus:ring-tremor-brand-muted dark:border-dark-tremor-border dark:bg-dark-tremor-background dark:text-dark-tremor-brand dark:shadow-dark-tremor-input dark:focus:ring-dark-tremor-brand-muted"
                    />
                  </div>
                  <div className="ml-3 text-tremor-default leading-6">
                    <label
                      htmlFor="checkbox-name-3"
                      className="font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong"
                    >
                      Enable email notifications for model deployment activities
                    </label>
                    <p
                      id="checkbox-name-3-description"
                      className="text-tremor-content dark:text-dark-tremor-content"
                    >
                      Labore et dolore magna aliquyam erat. Lorem ipsum dolor
                      sit amet, consetetur sadipscing elitr.{' '}
                      <a
                        href="#"
                        className="inline-flex items-center gap-1 text-tremor-default text-tremor-brand hover:underline hover:underline-offset-4 dark:text-dark-tremor-brand"
                      >
                        Go to email settings
                        <RiExternalLinkLine
                          className="size-4"
                          aria-hidden={true}
                        />
                      </a>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <Divider className="my-10" />
          <div className="flex items-center justify-end space-x-4">
            <button
              type="button"
              className="whitespace-nowrap rounded-tremor-small px-4 py-2.5 text-tremor-default font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="whitespace-nowrap rounded-tremor-small bg-tremor-brand px-4 py-2.5 text-tremor-default font-medium text-tremor-brand-inverted shadow-tremor-input hover:bg-tremor-brand-emphasis dark:bg-dark-tremor-brand dark:text-dark-tremor-brand-inverted dark:shadow-dark-tremor-input dark:hover:bg-dark-tremor-brand-emphasis"
            >
              Save settings
            </button>
          </div>
        </form>
      </TabGroup>
    </>
  );
}