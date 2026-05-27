// 'use client';

import { RiExternalLinkLine } from '@remixicon/react';
import {
  Card,
  CategoryBar,
  Divider,
  Tab,
  TabGroup,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  TabList,
} from '@tremor/react';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

const data = [
  {
    date: 'Dec 23',
    description: 'Venture debt loan repayment',
    account: 'Calantis business account',
    amount: '-$1,200',
    changeType: 'negative',
  },
  {
    date: 'Nov 23',
    description: 'Venture debt loan repayment',
    account: 'Calantis business account',
    amount: '-$2,200',
    changeType: 'negative',
  },
  {
    date: 'Oct 23',
    description: 'Venture debt loan repayment',
    account: 'Calantis business account',
    amount: '-$1,200',
    changeType: 'negative',
  },
  {
    date: 'Sep 23',
    description: 'Venture debt loan funding',
    account: 'Calantis business account',
    amount: '+$5,000,000',
    changeType: 'positive',
  },
];

export default function Example() {
  return (
    <>
      <h3 className="text-tremor-title font-bold text-tremor-content-strong dark:text-dark-tremor-content-strong">
        Capital
      </h3>
      <p className="mt-2 text-tremor-default leading-6 text-tremor-content dark:text-dark-tremor-content">
        Analyze and manage your venture debt and balance.
      </p>
      <TabGroup defaultIndex={0} className="mt-6">
        <TabList>
          <Tab>Venture Debt</Tab>
          <Tab>Capital Guide</Tab>
        </TabList>
      </TabGroup>
      {/* Content below only for demo purpose placed outside of <Tab> component. Add <TabPanels>, <TabPanel> to make it functional and to add content for other tabs */}
      <div className="mt-10 grid max-w-7xl grid-cols-1 gap-8 md:grid-cols-3">
        <Card className="md:col-span-2">
          <h4 className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
            Outstanding balance
          </h4>
          <p className="mt-1 text-tremor-metric font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
            $5,450,000
          </p>
          <CategoryBar
            values={[73, 22, 5]}
            colors={['blue', 'cyan', 'fuchsia']}
            showLabels={false}
            className="mt-6"
          />
          <ul
            role="list"
            className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2"
          >
            <li className="flex items-center space-x-2">
              <span
                className="size-3 shrink-0 rounded-sm bg-blue-500"
                aria-hidden={true}
              />
              <span className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                <span className="font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis">
                  $4M
                </span>{' '}
                outstanding
              </span>
            </li>
            <li className="flex items-center space-x-2">
              <span
                className="size-3 shrink-0 rounded-sm bg-cyan-500"
                aria-hidden={true}
              />
              <span className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                <span className="font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis">
                  $1.2M
                </span>{' '}
                available today
              </span>
            </li>
            <li className="flex items-center space-x-2">
              <span
                className="size-3 shrink-0 rounded-sm bg-fuchsia-500"
                aria-hidden={true}
              />
              <span className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                <span className="font-medium text-tremor-content-emphasis dark:text-dark-tremor-content-emphasis">
                  $0.25M
                </span>{' '}
                unavailable
              </span>
            </li>
          </ul>
          <Divider />
          <p className="mt-6 text-tremor-default font-medium text-tremor-content-strong dark:text-dark-tremor-content">
            Interest only ends Jan 4, 2024
          </p>
          <div className="mt-4 rounded-lg bg-tremor-background-muted p-4 dark:bg-dark-tremor-background-muted">
            <p className="flex flex-wrap justify-between gap-4 text-tremor-default leading-6 text-tremor-content dark:text-dark-tremor-content">
              Next payment of $3,200 due Jan 1, 2024.
              <a
                href="#"
                className="inline-flex items-center gap-1 text-tremor-brand hover:underline hover:underline-offset-4 dark:text-dark-tremor-brand"
              >
                Learn more
                <RiExternalLinkLine className="size-4" aria-hidden={true} />
              </a>
            </p>
          </div>
        </Card>
        <div className="md:col-span-1 md:p-6">
          <h4 className="font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong">
            Questions?
          </h4>
          <p className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
            Contact your financial advisor
          </p>
          <div className="mt-6 flex items-center space-x-4">
            <span
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-tremor-full bg-tremor-background-subtle text-tremor-default font-medium text-tremor-brand dark:bg-dark-tremor-background-subtle dark:text-dark-tremor-brand"
              aria-hidden={true}
            >
              EL
            </span>
            <div>
              <p className="text-tremor-default font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong">
                Emily Liftburg
              </p>
              <a
                href="mailto:#"
                className="mt-0.5 block text-tremor-default text-tremor-brand dark:text-dark-tremor-brand"
              >
                emily.liftburg@company.com
              </a>
            </div>
          </div>
        </div>
      </div>
      <p className="mt-14 font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong">
        Transactions
      </p>
      <Table className="mt-8">
        <TableHead>
          <TableRow className="border-b border-tremor-border dark:border-dark-tremor-border">
            <TableHeaderCell className="text-tremor-content-strong dark:text-dark-tremor-content-strong">
              Date
            </TableHeaderCell>
            <TableHeaderCell className="text-tremor-content-strong dark:text-dark-tremor-content-strong">
              Description
            </TableHeaderCell>
            <TableHeaderCell className="text-tremor-content-strong dark:text-dark-tremor-content-strong">
              Account
            </TableHeaderCell>
            <TableHeaderCell className="text-right text-tremor-content-strong dark:text-dark-tremor-content-strong">
              Amount
            </TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((item) => (
            <TableRow key={item.date}>
              <TableCell className="font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong">
                {item.date}
              </TableCell>
              <TableCell>{item.description}</TableCell>
              <TableCell>{item.account}</TableCell>
              <TableCell className="text-right">
                <span
                  className={classNames(
                    item.changeType === 'positive'
                      ? 'text-emerald-700 dark:text-emerald-500'
                      : 'text-tremor-content-strong dark:text-dark-tremor-content-strong',
                    'font-medium',
                  )}
                >
                  {item.amount}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}