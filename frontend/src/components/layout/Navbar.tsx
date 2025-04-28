import { Fragment } from 'react';
import { Menu, MenuButton, MenuItem, MenuItems, Transition, Disclosure, DisclosureButton, DisclosurePanel} from '@headlessui/react';
import { ChevronDownIcon, Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';
import { Link } from '@tanstack/react-router';

const navigation = [
  { name: 'Agents', href: '/agents' },
];

export const Navbar = (): React.ReactElement => {
  return (
    <Disclosure as="nav" className="w-full bg-white shadow-sm border-b-[3px] border-black px-4 z-20 sticky top-0 my-4">
      {({ open }) => (
        <>
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 justify-between">
              <div className="flex items-center">
                {/* Logo */}
                <Link className="flex flex-shrink-0 items-center" to="/" >
                  <img
                    alt="Logo"
                    className="h-8 w-8"
                    src="/images/favicons/favicon-192x192.png"
                  />
                  <span className="ml-2 text-xl font-bold text-gray-900">Mister Agent </span><span className="font-bold text-[#FE4A60]">Arena</span>
                </Link>
              </div>

              {/* Desktop menu */}
              <div className="hidden sm:flex sm:items-center">
                {navigation.map((item) => (
                  item.items ? (
                    <Menu key={item.name} as="div" className="relative ml-4">
                      <MenuButton className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900">
                        {item.name}
                        <ChevronDownIcon className="ml-1 h-4 w-4" />
                      </MenuButton>
                      <Transition
                        as={Fragment}
                        enter="transition ease-out duration-100"
                        enterFrom="transform opacity-0 scale-95"
                        enterTo="transform opacity-100 scale-100"
                        leave="transition ease-in duration-75"
                        leaveFrom="transform opacity-100 scale-100"
                        leaveTo="transform opacity-0 scale-95"
                      >
                        <MenuItems className="absolute right-0 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-30">
                          {item.items.map((subItem) => (
                            <MenuItem key={subItem.name}>
                              {({ focus }) => (
                                <Link
                                  key={subItem.name}
                                  to={subItem.href}
                                  className={`${
                                    focus ? 'bg-gray-100' : ''
                                  } block px-4 py-2 text-sm text-gray-700`}
                                >
                                  {subItem.name}
                                </Link>
                              )}
                            </MenuItem>
                          ))}
                        </MenuItems>
                      </Transition>
                    </Menu>
                  ) : (
                    <Link
                      key={item.name}
                      className="ml-4 px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                      to={item.href}
                    >
                      {item.name}
                    </Link>
                  )
                ))}
              </div>

              {/* Mobile menu button */}
              <div className="flex items-center sm:hidden">
                <DisclosureButton className="inline-flex items-center justify-center rounded-md p-2 text-gray-700 hover:bg-gray-100 hover:text-gray-900">
                  {open ? (
                    <XMarkIcon className="block h-6 w-6" />
                  ) : (
                    <Bars3Icon className="block h-6 w-6" />
                  )}
                </DisclosureButton>
              </div>
            </div>
          </div>

          {/* Mobile menu panel */}
          <DisclosurePanel className="sm:hidden">
            <div className="space-y-1 px-2 pb-3 pt-2">
              {navigation.map((item) => (
                item.items ? (
                  <Disclosure
                    key={item.name}
                    as="div"
                    className="space-y-1"
                  >
                    {({ open }) => (
                      <>
                        <DisclosureButton className="flex w-full items-center justify-between rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900">
                          <span>{item.name}</span>
                          <ChevronDownIcon
                            className={`${open ? 'transform rotate-180' : ''} h-5 w-5`}
                          />
                        </DisclosureButton>
                        <DisclosurePanel className="space-y-1 px-4">
                          {item.items.map((subItem) => (
                            <Link
                              key={subItem.name}
                              className="block rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                              to={subItem.href}
                            >
                              {subItem.name}
                            </Link>
                          ))}
                        </DisclosurePanel>
                      </>
                    )}
                  </Disclosure>
                ) : (
                  <Link
                    key={item.name}
                    className="block rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    to={item.href}
                  >
                    {item.name}
                  </Link>
                )
              ))}
            </div>
          </DisclosurePanel>
        </>
      )}
    </Disclosure>
  );
}; 