// 'use client';

import { RiExternalLinkLine } from '@remixicon/react';
import { Card, Divider, Switch, Tab, TabGroup, TabList } from '@tremor/react';

export default function Example() {
  return (
    <>
      <h3 className="text-tremor-title font-bold text-tremor-content-strong dark:text-dark-tremor-content-strong">
        General
      </h3>
      <p className="mt-2 text-tremor-default leading-6 text-tremor-content dark:text-dark-tremor-content">
        Manage your personal details, workspace governance and notifications.
      </p>
      <TabGroup defaultIndex={2} className="mt-6">
        <TabList>
          <Tab>Account details</Tab>
          <Tab>Users</Tab>
          <Tab>Add-Ons</Tab>
        </TabList>
        {/* Content below only for demo purpose placed outside of <Tab> component. Add <TabPanels>, <TabPanel> to make it functional and to add content for other tabs */}
        <div className="max-w-3xl">
          <h3 className="mt-8 font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
            Upgrade options
          </h3>
          <p className="mt-2 text-tremor-default text-tremor-content dark:text-dark-tremor-content">
            Do more with your data and unlock new insights with our advanced
            features and add-ons.
          </p>
          <Divider className="my-10" />
          <form action="#" method="POST">
            <div className="space-y-6">
              <Card>
                <p className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                  $25/month
                </p>
                <h4 className="mt-4 font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
                  Query Caching
                </h4>
                <p className="mt-2 text-tremor-default leading-6 text-tremor-content dark:text-dark-tremor-content">
                  Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed
                  diam nonumy eirmod tempor invidunt ut labore et dolore magna
                  aliquyam erat.
                </p>
                <Divider />
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Switch id="upgrade-1" name="upgrade-1" />
                    <label
                      htmlFor="upgrade-1"
                      className="text-tremor-default text-tremor-content dark:text-dark-tremor-content"
                    >
                      Activate <span className="sr-only">Query Caching</span>
                    </label>
                  </div>
                  <a
                    href="#"
                    className="inline-flex items-center gap-1 text-tremor-default text-tremor-brand hover:underline hover:underline-offset-4 dark:text-dark-tremor-brand"
                  >
                    Learn more
                    <RiExternalLinkLine className="size-4" aria-hidden={true} />
                  </a>
                </div>
              </Card>
              <Card>
                <p className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                  $100/month
                </p>
                <h4 className="mt-4 font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
                  Advanced Bot Protection
                </h4>
                <p className="mt-2 text-tremor-default leading-6 text-tremor-content dark:text-dark-tremor-content">
                  Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed
                  diam nonumy eirmod tempor invidunt ut labore et dolore magna
                  aliquyam erat.
                </p>
                <Divider />
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Switch id="upgrade-2" name="upgrade-2" />
                    <label
                      htmlFor="upgrade-2"
                      className="text-tremor-default text-tremor-content dark:text-dark-tremor-content"
                    >
                      Activate{' '}
                      <span className="sr-only">Advanced Bot Protection</span>
                    </label>
                  </div>
                  <a
                    href="#"
                    className="inline-flex items-center gap-1 text-tremor-default text-tremor-brand hover:underline hover:underline-offset-4 dark:text-dark-tremor-brand"
                  >
                    Learn more
                    <RiExternalLinkLine className="size-4" aria-hidden={true} />
                  </a>
                </div>
              </Card>
              <Card>
                <p className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                  $90/month
                </p>
                <h4 className="mt-4 font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
                  Observability Analytics
                </h4>
                <p className="mt-2 text-tremor-default leading-6 text-tremor-content dark:text-dark-tremor-content">
                  Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed
                  diam nonumy eirmod tempor invidunt ut labore et dolore magna
                  aliquyam erat.
                </p>
                <Divider />
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Switch id="upgrade-3" name="upgrade-3" />
                    <label
                      htmlFor="upgrade-3"
                      className="text-tremor-default text-tremor-content dark:text-dark-tremor-content"
                    >
                      Activate{' '}
                      <span className="sr-only">Observability Analytics</span>
                    </label>
                  </div>
                  <a
                    href="#"
                    className="inline-flex items-center gap-1 text-tremor-default text-tremor-brand hover:underline hover:underline-offset-4 dark:text-dark-tremor-brand"
                  >
                    Learn more
                    <RiExternalLinkLine className="size-4" aria-hidden={true} />
                  </a>
                </div>
              </Card>
            </div>
            <Divider />
            <div className="flex justify-end">
              <button
                type="submit"
                className="whitespace-nowrap rounded-tremor-small bg-tremor-brand px-4 py-2.5 text-tremor-default font-medium text-tremor-brand-inverted shadow-tremor-input hover:bg-tremor-brand-emphasis dark:bg-dark-tremor-brand dark:text-dark-tremor-brand-inverted dark:shadow-dark-tremor-input dark:hover:bg-dark-tremor-brand-emphasis"
              >
                Upgrade plan
              </button>
            </div>
          </form>
        </div>
      </TabGroup>
    </>
  );
}