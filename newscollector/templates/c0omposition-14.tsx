// 'use client';

import {
  RiBuildingFill,
  RiMapPin2Fill,
  RiSettings3Line,
  RiTimeLine,
  RiTruckLine,
  RiUserFill,
} from '@remixicon/react';
import {
  Card,
  Divider,
  ProgressCircle,
  Tab,
  TabGroup,
  TabList,
  TabPanel,
  TabPanels,
} from '@tremor/react';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

const data = [
  {
    status: 'In progress',
    icon: RiSettings3Line,
    iconColor: 'text-blue-500',
    orders: [
      {
        item: 'Printer Laser Jet Pro',
        company: 'Big Tech Ltd.',
        location: 'Paris, France',
        contact: 'Lena Stone',
        fulfillmentActual: 8,
        fulfillmentTotal: 10,
        lastUpdated: '2min ago',
      },
      {
        item: 'LED Monitor',
        company: 'Bitclick Holding',
        location: 'Zurich, Switzerland',
        contact: 'Matthias Ruedi',
        fulfillmentActual: 3,
        fulfillmentTotal: 4,
        lastUpdated: '5min ago',
      },
      {
        item: 'Conference Speaker',
        company: 'Cornerstone LLC',
        location: 'Frankfurt, Germany',
        contact: 'David Mueller',
        fulfillmentActual: 2,
        fulfillmentTotal: 4,
        lastUpdated: '10d ago',
      },
    ],
  },
  {
    status: 'Delivering',
    icon: RiTruckLine,
    iconColor: 'text-emerald-500',
    orders: [
      {
        item: 'OLED 49" Monitor',
        company: 'Walders AG',
        location: 'St. Gallen, Switzerland',
        contact: 'Patrick Doe',
        fulfillmentActual: 5,
        fulfillmentTotal: 6,
        lastUpdated: '4d ago',
      },
      {
        item: 'Portable Power Station',
        company: 'Lake View GmbH',
        location: 'Lucerne, Switzerland',
        contact: 'Marco Smith',
        fulfillmentActual: 5,
        fulfillmentTotal: 8,
        lastUpdated: '1d ago',
      },
      {
        item: 'Office headset (Wireless)',
        company: 'Cornerstone LLC',
        location: 'St. Anton, Austria',
        contact: 'Peter Batt',
        fulfillmentActual: 1,
        fulfillmentTotal: 2,
        lastUpdated: '7d ago',
      },
      {
        item: 'Smart Home Security System',
        company: 'SecureTech Solutions AG',
        location: 'Munich, Germany',
        contact: 'Thomas Schneider',
        fulfillmentActual: 3,
        fulfillmentTotal: 4,
        lastUpdated: '2h ago',
      },
      {
        item: 'Gaming Laptop Super Screen 14" (This is a super long edge case with many numbers)',
        company: 'Tech Master Ltd.',
        location: 'Aspen, USA',
        contact: 'Joe Ross',
        fulfillmentActual: 9,
        fulfillmentTotal: 10,
        lastUpdated: '1h ago',
      },
    ],
  },
  {
    status: 'Delayed',
    icon: RiTimeLine,
    iconColor: 'text-orange-500',
    orders: [
      {
        item: 'External SSD Portable',
        company: 'Waterbridge Associates Inc.',
        location: 'New York, USA',
        contact: 'Adam Taylor',
        fulfillmentActual: 4,
        fulfillmentTotal: 12,
        lastUpdated: '1d ago',
      },
      {
        item: 'Portable Scanner V600',
        company: 'Hotel Stars GmbH',
        location: 'Chur, Switzerland',
        contact: 'Elias Jones',
        fulfillmentActual: 5,
        fulfillmentTotal: 10,
        lastUpdated: '4d ago',
      },
    ],
  },
];

const statusColor = {
  'In progress':
    'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-400/10 dark:text-blue-400 dark:ring-blue-400/20',
  Delivering:
    'bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-400/10 dark:text-emerald-400 dark:ring-emerald-400/20',
  Delayed:
    'bg-orange-50 text-orange-700 ring-orange-600/20 dark:bg-orange-400/10 dark:text-orange-400 dark:ring-orange-400/20',
};

export default function Example() {
  return (
    <>
      <Card className="bg-tremor-background-muted p-0 dark:bg-dark-tremor-background-muted">
        <div className="p-6">
          <h3 className="text-tremor-title font-semibold text-tremor-content-strong dark:text-dark-tremor-content-strong">
            Orders
          </h3>
          <p className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
            Check status of recent orders
          </p>
        </div>
        <TabGroup>
          <TabList className="bg-tremor-background-muted px-6 dark:bg-dark-tremor-background-muted">
            {data.map((category) => (
              <Tab
                key={category.status}
                className="pb-2.5 font-medium hover:border-gray-300"
              >
                <div className="sm:flex sm:items-center sm:space-x-2">
                  <category.icon
                    className={classNames(
                      category.iconColor,
                      'hidden size-5 sm:block',
                    )}
                    aria-hidden={true}
                  />
                  <span className="ui-selected:text-tremor-content-strong ui-selected:dark:text-dark-tremor-content-strong">
                    {category.status}
                  </span>
                  <span className="hidden rounded-tremor-small bg-tremor-background px-2 py-1 text-xs font-semibold tabular-nums ring-1 ring-inset ring-tremor-ring ui-selected:text-tremor-content-emphasis dark:bg-dark-tremor-background-muted dark:ring-dark-tremor-ring ui-selected:dark:text-dark-tremor-content-emphasis sm:block">
                    {category.orders.length}
                  </span>
                </div>
              </Tab>
            ))}
          </TabList>
          <TabPanels className="bg-tremor-background pt-2 dark:bg-dark-tremor-background">
            {data.map((category) => (
              <TabPanel
                key={category.status}
                className="space-y-4 px-6 pb-6 pt-2"
              >
                {category.orders.map((order) => (
                  <Card key={order.item}>
                    <div className="flex items-center justify-between space-x-4 sm:justify-start sm:space-x-2">
                      <h4 className="truncate text-tremor-default font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong">
                        {order.item}
                      </h4>
                      <span
                        className={classNames(
                          statusColor[category.status],
                          'inline-flex items-center whitespace-nowrap rounded px-1.5 py-0.5 text-tremor-label font-medium ring-1 ring-inset',
                        )}
                        aria-hidden={true}
                      >
                        {category.status}
                      </span>
                    </div>
                    <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-4">
                      <div className="flex items-center space-x-1.5">
                        <RiBuildingFill
                          className="size-5 text-tremor-content-subtle dark:text-dark-tremor-content-subtle"
                          aria-hidden={true}
                        />
                        <p className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                          {order.company}
                        </p>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <RiMapPin2Fill
                          className="size-5 text-tremor-content-subtle dark:text-dark-tremor-content-subtle"
                          aria-hidden={true}
                        />
                        <p className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                          {order.location}
                        </p>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <RiUserFill
                          className="size-5 text-tremor-content-subtle dark:text-dark-tremor-content-subtle"
                          aria-hidden={true}
                        />
                        <p className="text-tremor-default text-tremor-content dark:text-dark-tremor-content">
                          {order.contact}
                        </p>
                      </div>
                    </div>
                    <Divider />
                    <div className="block sm:flex sm:items-center sm:justify-between sm:space-x-2">
                      <div className="flex items-center space-x-2">
                        <ProgressCircle
                          value={
                            (order.fulfillmentActual / order.fulfillmentTotal) *
                            100
                          }
                          radius={9}
                          strokeWidth={3.5}
                        />
                        <p className="text-tremor-default font-medium text-tremor-content-strong dark:text-dark-tremor-content-strong">
                          Fulfillment controls ({order.fulfillmentActual}/
                          {order.fulfillmentTotal})
                        </p>
                      </div>
                      <p className="mt-2 text-tremor-default text-tremor-content dark:text-dark-tremor-content sm:mt-0">
                        Updated {order.lastUpdated}
                      </p>
                    </div>
                  </Card>
                ))}
              </TabPanel>
            ))}
          </TabPanels>
        </TabGroup>
      </Card>
    </>
  );
}