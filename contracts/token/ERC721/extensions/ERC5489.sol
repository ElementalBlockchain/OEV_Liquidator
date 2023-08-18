//SPDX-License-Identifier: CC0-1.0
pragma solidity ^0.8.0;

import '../../defi_infrastructure/openzeppelin-contracts/contracts/token/ERC721/extensions/ERC721Enumerable.sol/';
import "../../defi_infrastructure/openzeppelin-contracts/contracts/access/Ownable.sol";
import "../../defi_infrastructure/openzeppelin-contracts/contracts/utils/Base64.sol";

interface IERC5489 {
    /**
     * @dev this event emits when the slot on `tokenId` is authorzized to `slotManagerAddr`
     */
    event SlotAuthorizationCreated(uint256 indexed tokenId, address indexed slotManagerAddr);

    /**
     * @dev this event emits when the authorization on slot `slotManagerAddr` of token `tokenId` is revoked.
     * So, the corresponding DApp can handle this to stop on-going incentives or rights
     */
    event SlotAuthorizationRevoked(uint256 indexed tokenId, address indexed slotManagerAddr);

    /**
     * @dev this event emits when the uri on slot `slotManagerAddr` of token `tokenId` has been updated to `uri`.
     */
    event SlotUriUpdated(uint256 indexed tokenId, address indexed slotManagerAddr, string uri);

    /**
     * @dev
     * Authorize a hyperlink slot on `tokenId` to address `slotManagerAddr`.
     * Indeed slot is an entry in a map whose key is address `slotManagerAddr`.
     * Only the address `slotManagerAddr` can manage the specific slot.
     * This method will emit SlotAuthorizationCreated event
     */
    function authorizeSlotTo(uint256 tokenId, address slotManagerAddr) external;

    /**
     * @dev
     * Revoke the authorization of the slot indicated by `slotManagerAddr` on token `tokenId`
     * This method will emit SlotAuthorizationRevoked event
     */
    function revokeAuthorization(uint256 tokenId, address slotManagerAddr) external;

    /**
     * @dev
     * Revoke all authorizations of slot on token `tokenId`
     * This method will emit SlotAuthorizationRevoked event for each slot
     */
    function revokeAllAuthorizations(uint256 tokenId) external;

    /**
     * @dev
     * Set uri for a slot on a token, which is indicated by `tokenId` and `slotManagerAddr`
     * Only the address with authorization through {authorizeSlotTo} can manipulate this slot.
     * This method will emit SlotUriUpdated event
     */
    function setSlotUri(
        uint256 tokenId,
        string calldata newUri
    ) external;

    /**
     * @dev Throws if `tokenId` is not a valid NFT. URIs are defined in RFC 3986.
     * The URI MUST point to a JSON file that conforms to the "EIP5489 Metadata JSON schema".
     *
     * returns the latest uri of an slot on a token, which is indicated by `tokenId`, `slotManagerAddr`
     */
    function getSlotUri(uint256 tokenId, address slotManagerAddr)
    external
    view
    returns (string memory);
}

library EnumerableSet {
    // To implement this library for multiple types with as little code
    // repetition as possible, we write it in terms of a generic Set type with
    // bytes32 values.
    // The Set implementation uses private functions, and user-facing
    // implementations (such as AddressSet) are just wrappers around the
    // underlying Set.
    // This means that we can only create new EnumerableSets for types that fit
    // in bytes32.

    struct Set {
        // Storage of set values
        bytes32[] _values;
        // Position of the value in the `values` array, plus 1 because index 0
        // means a value is not in the set.
        mapping(bytes32 => uint256) _indexes;
    }

    /**
     * @dev Add a value to a set. O(1).
     *
     * Returns true if the value was added to the set, that is if it was not
     * already present.
     */
    function _add(Set storage set, bytes32 value) private returns (bool) {
        if (!_contains(set, value)) {
            set._values.push(value);
            // The value is stored at length-1, but we add 1 to all indexes
            // and use 0 as a sentinel value
            set._indexes[value] = set._values.length;
            return true;
        } else {
            return false;
        }
    }

    /**
     * @dev Removes a value from a set. O(1).
     *
     * Returns true if the value was removed from the set, that is if it was
     * present.
     */
    function _remove(Set storage set, bytes32 value) private returns (bool) {
        // We read and store the value's index to prevent multiple reads from the same storage slot
        uint256 valueIndex = set._indexes[value];

        if (valueIndex != 0) {
            // Equivalent to contains(set, value)
            // To delete an element from the _values array in O(1), we swap the element to delete with the last one in
            // the array, and then remove the last element (sometimes called as 'swap and pop').
            // This modifies the order of the array, as noted in {at}.

            uint256 toDeleteIndex = valueIndex - 1;
            uint256 lastIndex = set._values.length - 1;

            if (lastIndex != toDeleteIndex) {
                bytes32 lastValue = set._values[lastIndex];

                // Move the last value to the index where the value to delete is
                set._values[toDeleteIndex] = lastValue;
                // Update the index for the moved value
                set._indexes[lastValue] = valueIndex; // Replace lastValue's index to valueIndex
            }

            // Delete the slot where the moved value was stored
            set._values.pop();

            // Delete the index for the deleted slot
            delete set._indexes[value];

            return true;
        } else {
            return false;
        }
    }

    /**
     * @dev Returns true if the value is in the set. O(1).
     */
    function _contains(Set storage set, bytes32 value) private view returns (bool) {
        return set._indexes[value] != 0;
    }

    /**
     * @dev Returns the number of values on the set. O(1).
     */
    function _length(Set storage set) private view returns (uint256) {
        return set._values.length;
    }

    /**
     * @dev Returns the value stored at position `index` in the set. O(1).
     *
     * Note that there are no guarantees on the ordering of values inside the
     * array, and it may change when more values are added or removed.
     *
     * Requirements:
     *
     * - `index` must be strictly less than {length}.
     */
    function _at(Set storage set, uint256 index) private view returns (bytes32) {
        return set._values[index];
    }

    /**
     * @dev Return the entire set in an array
     *
     * WARNING: This operation will copy the entire storage to memory, which can be quite expensive. This is designed
     * to mostly be used by view accessors that are queried without any gas fees. Developers should keep in mind that
     * this function has an unbounded cost, and using it as part of a state-changing function may render the function
     * uncallable if the set grows to a point where copying to memory consumes too much gas to fit in a block.
     */
    function _values(Set storage set) private view returns (bytes32[] memory) {
        return set._values;
    }

    // Bytes32Set

    struct Bytes32Set {
        Set _inner;
    }

    /**
     * @dev Add a value to a set. O(1).
     *
     * Returns true if the value was added to the set, that is if it was not
     * already present.
     */
    function add(Bytes32Set storage set, bytes32 value) internal returns (bool) {
        return _add(set._inner, value);
    }

    /**
     * @dev Removes a value from a set. O(1).
     *
     * Returns true if the value was removed from the set, that is if it was
     * present.
     */
    function remove(Bytes32Set storage set, bytes32 value) internal returns (bool) {
        return _remove(set._inner, value);
    }

    /**
     * @dev Returns true if the value is in the set. O(1).
     */
    function contains(Bytes32Set storage set, bytes32 value) internal view returns (bool) {
        return _contains(set._inner, value);
    }

    /**
     * @dev Returns the number of values in the set. O(1).
     */
    function length(Bytes32Set storage set) internal view returns (uint256) {
        return _length(set._inner);
    }

    /**
     * @dev Returns the value stored at position `index` in the set. O(1).
     *
     * Note that there are no guarantees on the ordering of values inside the
     * array, and it may change when more values are added or removed.
     *
     * Requirements:
     *
     * - `index` must be strictly less than {length}.
     */
    function at(Bytes32Set storage set, uint256 index) internal view returns (bytes32) {
        return _at(set._inner, index);
    }

    /**
     * @dev Return the entire set in an array
     *
     * WARNING: This operation will copy the entire storage to memory, which can be quite expensive. This is designed
     * to mostly be used by view accessors that are queried without any gas fees. Developers should keep in mind that
     * this function has an unbounded cost, and using it as part of a state-changing function may render the function
     * uncallable if the set grows to a point where copying to memory consumes too much gas to fit in a block.
     */
    function values(Bytes32Set storage set) internal view returns (bytes32[] memory) {
        bytes32[] memory store = _values(set._inner);
        bytes32[] memory result;

        /// @solidity memory-safe-assembly
        assembly {
            result := store
        }

        return result;
    }

    // AddressSet

    struct AddressSet {
        Set _inner;
    }

    /**
     * @dev Add a value to a set. O(1).
     *
     * Returns true if the value was added to the set, that is if it was not
     * already present.
     */
    function add(AddressSet storage set, address value) internal returns (bool) {
        return _add(set._inner, bytes32(uint256(uint160(value))));
    }

    /**
     * @dev Removes a value from a set. O(1).
     *
     * Returns true if the value was removed from the set, that is if it was
     * present.
     */
    function remove(AddressSet storage set, address value) internal returns (bool) {
        return _remove(set._inner, bytes32(uint256(uint160(value))));
    }

    /**
     * @dev Returns true if the value is in the set. O(1).
     */
    function contains(AddressSet storage set, address value) internal view returns (bool) {
        return _contains(set._inner, bytes32(uint256(uint160(value))));
    }

    /**
     * @dev Returns the number of values in the set. O(1).
     */
    function length(AddressSet storage set) internal view returns (uint256) {
        return _length(set._inner);
    }

    /**
     * @dev Returns the value stored at position `index` in the set. O(1).
     *
     * Note that there are no guarantees on the ordering of values inside the
     * array, and it may change when more values are added or removed.
     *
     * Requirements:
     *
     * - `index` must be strictly less than {length}.
     */
    function at(AddressSet storage set, uint256 index) internal view returns (address) {
        return address(uint160(uint256(_at(set._inner, index))));
    }

    /**
     * @dev Return the entire set in an array
     *
     * WARNING: This operation will copy the entire storage to memory, which can be quite expensive. This is designed
     * to mostly be used by view accessors that are queried without any gas fees. Developers should keep in mind that
     * this function has an unbounded cost, and using it as part of a state-changing function may render the function
     * uncallable if the set grows to a point where copying to memory consumes too much gas to fit in a block.
     */
    function values(AddressSet storage set) internal view returns (address[] memory) {
        bytes32[] memory store = _values(set._inner);
        address[] memory result;

        /// @solidity memory-safe-assembly
        assembly {
            result := store
        }

        return result;
    }

    // UintSet

    struct UintSet {
        Set _inner;
    }

    /**
     * @dev Add a value to a set. O(1).
     *
     * Returns true if the value was added to the set, that is if it was not
     * already present.
     */
    function add(UintSet storage set, uint256 value) internal returns (bool) {
        return _add(set._inner, bytes32(value));
    }

    /**
     * @dev Removes a value from a set. O(1).
     *
     * Returns true if the value was removed from the set, that is if it was
     * present.
     */
    function remove(UintSet storage set, uint256 value) internal returns (bool) {
        return _remove(set._inner, bytes32(value));
    }

    /**
     * @dev Returns true if the value is in the set. O(1).
     */
    function contains(UintSet storage set, uint256 value) internal view returns (bool) {
        return _contains(set._inner, bytes32(value));
    }

    /**
     * @dev Returns the number of values in the set. O(1).
     */
    function length(UintSet storage set) internal view returns (uint256) {
        return _length(set._inner);
    }

    /**
     * @dev Returns the value stored at position `index` in the set. O(1).
     *
     * Note that there are no guarantees on the ordering of values inside the
     * array, and it may change when more values are added or removed.
     *
     * Requirements:
     *
     * - `index` must be strictly less than {length}.
     */
    function at(UintSet storage set, uint256 index) internal view returns (uint256) {
        return uint256(_at(set._inner, index));
    }

    /**
     * @dev Return the entire set in an array
     *
     * WARNING: This operation will copy the entire storage to memory, which can be quite expensive. This is designed
     * to mostly be used by view accessors that are queried without any gas fees. Developers should keep in mind that
     * this function has an unbounded cost, and using it as part of a state-changing function may render the function
     * uncallable if the set grows to a point where copying to memory consumes too much gas to fit in a block.
     */
    function values(UintSet storage set) internal view returns (uint256[] memory) {
        bytes32[] memory store = _values(set._inner);
        uint256[] memory result;

        /// @solidity memory-safe-assembly
        assembly {
            result := store
        }

        return result;
    }
}

contract ERC5489 is IERC5489, ERC721Enumerable {
    using EnumerableSet for EnumerableSet.AddressSet;

    mapping(uint256 => EnumerableSet.AddressSet) tokenId2AuthroizedAddresses;
    mapping(uint256 => mapping(address=> string)) tokenId2Address2Value;
    mapping(uint256 => string) tokenId2ImageUri;

    string private _imageURI;
    string private _name;

    constructor() ERC721("Hyperlink NFT Collection", "HNFT") {}

    modifier onlyTokenOwner(uint256 tokenId) {
        require(_msgSender() == ownerOf(tokenId), "should be the token owner");
        _;
    }

    modifier onlySlotManager(uint256 tokenId) {
        require(_msgSender() == ownerOf(tokenId) || tokenId2AuthroizedAddresses[tokenId].contains(_msgSender()), "address should be authorized");
        _;
    }

    function setSlotUri(uint256 tokenId, string calldata value) override external onlySlotManager(tokenId) {
        tokenId2Address2Value[tokenId][_msgSender()] = value;

        emit SlotUriUpdated(tokenId, _msgSender(), value);
    }

    function getSlotUri(uint256 tokenId, address slotManagerAddr) override external view returns (string memory) {
        return tokenId2Address2Value[tokenId][slotManagerAddr];
    }

    function authorizeSlotTo(uint256 tokenId, address slotManagerAddr) override external onlyTokenOwner(tokenId) {
        require(!tokenId2AuthroizedAddresses[tokenId].contains(slotManagerAddr), "address already authorized");

        _authorizeSlotTo(tokenId, slotManagerAddr);
    }

    function _authorizeSlotTo(uint256 tokenId, address slotManagerAddr) private {
        tokenId2AuthroizedAddresses[tokenId].add(slotManagerAddr);
        emit SlotAuthorizationCreated(tokenId, slotManagerAddr);
    }

    function revokeAuthorization(uint256 tokenId, address slotManagerAddr) override external onlyTokenOwner(tokenId) {
        tokenId2AuthroizedAddresses[tokenId].remove(slotManagerAddr);
        delete tokenId2Address2Value[tokenId][slotManagerAddr];

        emit SlotAuthorizationRevoked(tokenId, slotManagerAddr);
    }

    function revokeAllAuthorizations(uint256 tokenId) override external onlyTokenOwner(tokenId) {
        for (uint256 i = tokenId2AuthroizedAddresses[tokenId].length() - 1;i > 0; i--) {
            address addr = tokenId2AuthroizedAddresses[tokenId].at(i);
            tokenId2AuthroizedAddresses[tokenId].remove(addr);
            delete tokenId2Address2Value[tokenId][addr];

            emit SlotAuthorizationRevoked(tokenId, addr);
        }

        if (tokenId2AuthroizedAddresses[tokenId].length() > 0) {
            address addr = tokenId2AuthroizedAddresses[tokenId].at(0);
            tokenId2AuthroizedAddresses[tokenId].remove(addr);
            delete tokenId2Address2Value[tokenId][addr];

            emit SlotAuthorizationRevoked(tokenId, addr);
        }
    }

    function isSlotManager(uint256 tokenId, address addr) public view returns (bool) {
        return tokenId2AuthroizedAddresses[tokenId].contains(addr);
    }

    // !!expensive, should call only when no gas is needed;
    function getSlotManagers(uint256 tokenId) external view returns (address[] memory) {
        return tokenId2AuthroizedAddresses[tokenId].values();
    }

    function _mintToken(uint256 tokenId, string calldata imageUri) private {
        _safeMint(msg.sender, tokenId);
        tokenId2ImageUri[tokenId] = imageUri;
    }

    function mint(string calldata imageUri) external {
        uint256 tokenId = totalSupply() + 1;
        _mintToken(tokenId, imageUri);
    }

    function mintAndAuthorizeTo(string calldata imageUri, address slotManagerAddr) external {
        uint256 tokenId = totalSupply() + 1;
        _mintToken(tokenId, imageUri);
        _authorizeSlotTo(tokenId, slotManagerAddr);
    }

    function tokenURI(uint256 _tokenId) public view override returns (string memory) {
        require(
            _exists(_tokenId),
            "URI query for nonexistent token"
        );

        return
            string(
                abi.encodePacked(
                    "data:application/json;base64,",
                    Base64.encode(
                        bytes(
                            abi.encodePacked(
                                '{"name":"',
                                abi.encodePacked(
                                    _name,
                                    " # ",
                                    Strings.toString(_tokenId)
                                ),
                                '",',
                                '"description":"Hyperlink NFT collection created with Parami Foundation"',
                                '}'
                            )
                        )
                    )
                )
            );
    }
}
